#include <vector>
#include <cmath>
#include <random>
#include <algorithm>
using namespace std;

struct Decoy {
    float x,y,amp,sigma;
};

class Terrain {
public:
    float world_half;
    float target_sigma;
    float target_x = 0.0f;
    float target_y = 0.0f;
    vector<Decoy> decoys;

    Terrain(float world_half = 380.0, float target_sigma = 140.0) : world_half(world_half), target_sigma(target_sigma) {}

    void set_target(float x, float y) {
        target_x = x;
        target_y = y;
    }

    void regenerate_decoys(int count) {
        decoys.clear();
        for (int i = 0; i < count; ++i) {
            Decoy d;
            d.x = ranf(-0.75f * world_half, 0.75f * world_half);
            d.y = ranf(-0.75f * world_half, 0.75f * world_half);
            d.amp = ranf(0.30f, 0.55f);
            d.sigma = ranf(55.0f, 100.0f);
            decoys.push_back(d);
        }
    }

    float fitness_at(float x, float y) const {
        float dx = x-target_x;
        float dy = y-target_y;
        float target_val = exp(-(dx*dx+dy*dy)/(2.0*target_sigma*target_sigma));
        float max_decoy_val = 0.0f;
        for (const auto& d: decoys) {
            float ddx = x-d.x;
            float ddy = y-d.y;
            float decoy_val = d.amp * exp(-(ddx*ddx+ddy*ddy)/(2.0*d.sigma*d.sigma));
            if (decoy_val>max_decoy_val) {
                max_decoy_val = decoy_val;
            }
        }
        return target_val + max_decoy_val * (1.0f - target_val);
    }

    float get_world_half() const { return world_half; }
    float get_target_x() const { return target_x; }
    float get_target_y() const { return target_y; }

private:
    mutable mt19937 rng{random_device{}()};
    float ranf(float min_val, float max_val) const {
        uniform_real_distribution<float> dist(min_val, max_val);
        return dist(rng);
    }
};