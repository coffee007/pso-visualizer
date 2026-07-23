#include "engine.hpp"
#include <algorithm>
using namespace std;

// Constructor
PSOEngine::PSOEngine(const Terrain& terrain, int num_particles, float v_max) 
    : terrain_(terrain), default_v_max_(v_max), num_particles_(num_particles), gen(rd()) {
    
    // Dynamically grab the WORLD_HALF you passed from Python!
    float wh = terrain_.get_world_half();
    
    // gridsize = {x_min, x_max, y_min, y_max}
    gridsize = {-wh, wh, -wh, wh};
    
    reset(num_particles_);
}

void PSOEngine::reset() {
    watch_active_ = false;
    reset(num_particles_);
}

void PSOEngine::reset(int new_num_particles) {
    int n = new_num_particles;
    pos.resize(n);
    vel.resize(n);
    bestpos.resize(n);
    perbest.assign(n, -1e9f);
    global_best = -1e9f;
    global_best_pos = {0.0f, 0.0f};
    uniform_real_distribution<float> disx(-default_v_max_, default_v_max_);
    uniform_real_distribution<float> disy(-default_v_max_, default_v_max_);
    uniform_real_distribution<float> dx(gridsize[0], gridsize[1]);
    uniform_real_distribution<float> dy(gridsize[2], gridsize[3]);

    for (int i = 0; i < n; i++)
    {
        vel[i][0]=disx(gen);vel[i][1] = disy(gen);
        pos[i][0]=dx(gen);pos[i][1] = dy(gen);
        bestpos[i]=pos[i];
        perbest[i]=f(pos[i][0], pos[i][1]);
        if(perbest[i] > global_best){
            global_best = perbest[i];
            global_best_pos = bestpos[i];
        }
    }
}

void PSOEngine::step(float w, float c1, float c2, float max_v) {
    int n = num_particles_;
    uniform_real_distribution<float> u(0,1);
    for (int i = 0; i<n; i++)
    {
        float x1=u(gen)*c2;
        float x2=u(gen)*c1; 
        float y1=u(gen)*c2;
        float y2=u(gen)*c1;

        vel[i][0] = w*vel[i][0]+x1*(global_best_pos[0]-pos[i][0])+x2*(bestpos[i][0]-pos[i][0]);
        vel[i][1] = w*vel[i][1]+y1*(global_best_pos[1]-pos[i][1])+y2*(bestpos[i][1]-pos[i][1]);

        //speed clamping is giving better visuals than individual component clamping
        float speed_sq = vel[i][0]*vel[i][0]+vel[i][1]*vel[i][1];
        if (max_v>0.0f && speed_sq>max_v*max_v) {
            float speed = std::sqrt(speed_sq);
            vel[i][0] = (vel[i][0]/speed)*max_v;
            vel[i][1] = (vel[i][1]/speed)*max_v;
        }

        pos[i][0] = max(min(vel[i][0]+pos[i][0],gridsize[1]),gridsize[0]);
        pos[i][1] = max(min(vel[i][1]+pos[i][1],gridsize[3]),gridsize[2]);
        float current_score = f(pos[i][0],pos[i][1]);
        if(current_score > perbest[i]){
            perbest[i] = current_score;
            bestpos[i] = {pos[i][0], pos[i][1]};
        }
        if(perbest[i] > global_best){
            global_best = perbest[i];
            global_best_pos = bestpos[i];
        }
    }
    if (watch_active_) {
        watch_countdown_--;
        if (watch_countdown_ <= 0) {
            if (global_best < 0.6f && watch_rounds_left_ > 0) {
                inject_scouts(0.25f);
                watch_countdown_ = 90;
                watch_rounds_left_--;
            } else {
                watch_active_ = false;
            }
        }
    }
}

void PSOEngine::inject_scouts(float frac) {
    int n = num_particles_;
    int n_scouts = std::max(1, (int)std::round(n * frac));
    float wh = terrain_.get_world_half();
    uniform_real_distribution<float> dpos(-wh, wh);
    uniform_real_distribution<float> u01(0.0f, 1.0f);

    vector<int> idx(n);
    for (int i = 0; i < n; i++) idx[i] = i;
    shuffle(idx.begin(), idx.end(), gen);

    for (int k = 0; k < n_scouts; k++) {
        int i = idx[k];
        pos[i][0] = dpos(gen); pos[i][1] = dpos(gen);
        float ang = u01(gen) * 6.2831853f, mag = (0.15f + u01(gen) * 0.45f) * default_v_max_;
        vel[i][0] = cos(ang) * mag; vel[i][1] = sin(ang) * mag;
        bestpos[i] = pos[i];
        perbest[i] = f(pos[i][0], pos[i][1]);
        if (perbest[i] > global_best) { global_best = perbest[i]; global_best_pos = bestpos[i]; }
    }
}

void PSOEngine::retarget() {
    int n = num_particles_;
    float wh = terrain_.get_world_half();
    const float jitter_frac = 0.12f, kick_lo = 0.15f, kick_hi = 0.6f, keep_vel_frac = 0.35f, scout_frac = 0.25f;

    int n_scouts = max(1, (int)round(n * scout_frac));
    vector<int> idx(n);
    for (int i = 0; i < n; i++) idx[i] = i;
    shuffle(idx.begin(), idx.end(), gen);
    vector<bool> is_scout(n, false);
    for (int k = 0; k<n_scouts; k++) is_scout[idx[k]] = true;

    uniform_real_distribution<float> u01(0.0f, 1.0f);
    for (int i = 0; i < n; i++) {
        float ang = u01(gen) * 6.2831853f;
        float mag = (kick_lo + u01(gen) * (kick_hi - kick_lo)) * default_v_max_;
        if (is_scout[i]) {
            pos[i][0] = gridsize[0] + u01(gen) * (gridsize[1] - gridsize[0]);
            pos[i][1] = gridsize[2] + u01(gen) * (gridsize[3] - gridsize[2]);
            vel[i][0] = cos(ang) * mag; vel[i][1] = sin(ang) * mag;
        } else {
            // Using the width of the grid to calculate the jitter radius instead of wh
            float width = gridsize[1] - gridsize[0];
            float radius = u01(gen) * jitter_frac * (width / 2.0f);
            
            // Clamp to gridsize, NOT wh
            pos[i][0] = max(min(pos[i][0] + cos(ang) * radius, gridsize[1]), gridsize[0]);
            pos[i][1] = max(min(pos[i][1] + sin(ang) * radius, gridsize[3]), gridsize[2]);
        }
    }

    global_best = -1e9f;
    for (int i = 0; i < n; i++) {
        bestpos[i] = pos[i];
        perbest[i] = f(pos[i][0], pos[i][1]);
        if (perbest[i] > global_best) { global_best = perbest[i]; global_best_pos = bestpos[i]; }
    }
    watch_active_ = true;
    watch_countdown_ = 90;
    watch_rounds_left_ = 2;
}

// Optimization function f(x,y)
float PSOEngine::f(float x, float y) const {
    return terrain_.fitness_at(x, y); 
}