#include "engine.hpp"
#include <algorithm>

using namespace std;

// Constructor
PSOEngine::PSOEngine(const Terrain& terrain, int num_particles, float v_max) 
    : terrain_(terrain), default_v_max_(v_max), num_particles_(num_particles), gen(rd()) {
    reset(num_particles_);
}

void PSOEngine::reset() {
    reset(num_particles_);
}

void PSOEngine::reset(int new_num_particles) {
    num_particles_ = new_num_particles;
    int n = num_particles_;
    
    pos.resize(n);
    vel.resize(n);
    bestpos.resize(n);
    perbest.assign(n, -1e9f);

    global_best = -1e9f;
    global_best_pos = {0.0f, 0.0f};

    // RNG Distributions based on grid boundaries and max velocity
    uniform_real_distribution<float> disx(-default_v_max_, default_v_max_);
    uniform_real_distribution<float> disy(-default_v_max_, default_v_max_);
    uniform_real_distribution<float> dx(gridsize[0], gridsize[1]);
    uniform_real_distribution<float> dy(gridsize[2], gridsize[3]);

    for (int i = 0; i < n; i++)
    {
        vel[i][0] = disx(gen); 
        vel[i][1] = disy(gen);
        pos[i][0] = dx(gen); 
        pos[i][1] = dy(gen);
        bestpos[i] = pos[i];
        perbest[i] = f(pos[i][0], pos[i][1]);

        if(perbest[i] > global_best){
            global_best = perbest[i];
            global_best_pos = bestpos[i];
        }
    }
}

void PSOEngine::step(float w, float c1, float c2, float max_v) {
    int n = num_particles_;
    uniform_real_distribution<float> u(0, 1);
    
    for (int i = 0; i < n; i++)
    {
        float x1 = u(gen) * c1;
        float x2 = u(gen) * c2; 
        float y1 = u(gen) * c1;
        float y2 = u(gen) * c2;

        vel[i][0] = w * vel[i][0] + x1 * (global_best_pos[0] - pos[i][0]) + x2 * (bestpos[i][0] - pos[i][0]);
        vel[i][1] = w * vel[i][1] + y1 * (global_best_pos[1] - pos[i][1]) + y2 * (bestpos[i][1] - pos[i][1]);
        
        // Optional velocity clamping to prevent explosive movement
        // Fix 2: Clamp the vector magnitude (circular clamp) instead of independent axes
        float speed_sq = vel[i][0] * vel[i][0] + vel[i][1] * vel[i][1];
        if (speed_sq > max_v * max_v) {
            float speed = std::sqrt(speed_sq);
            vel[i][0] = (vel[i][0] / speed) * max_v;
            vel[i][1] = (vel[i][1] / speed) * max_v;
        }

        pos[i][0] = max(min(vel[i][0] + pos[i][0], gridsize[1]), gridsize[0]);
        pos[i][1] = max(min(vel[i][1] + pos[i][1], gridsize[3]), gridsize[2]);

        float current_score = f(pos[i][0], pos[i][1]);

        if(current_score > perbest[i]){
            perbest[i] = current_score;
            bestpos[i] = {pos[i][0], pos[i][1]};
        }
        if(perbest[i] > global_best){
            global_best = perbest[i];
            global_best_pos = bestpos[i];
        }
    }
}

// Optimization function f(x,y)
float PSOEngine::f(float x, float y) const {
    return terrain_.fitness_at(x, y); 
}