#pragma once

#include "terrain.hpp"
#include <vector>
#include <array>
#include <random>

class PSOEngine {
public:
    PSOEngine(const Terrain& terrain, int num_particles = 200, float v_max = 7.0f);

    void reset();
    void reset(int new_num_particles);
    void step(float w = 0.729f, float c1 = 1.49445f, float c2 = 1.49445f, float max_v = -1.0f);

    // Getters matching the existing Python bindings
    int get_num_particles() const { return num_particles_; }
    const std::vector<std::array<float, 2>>& get_pos() const { return pos; }
    
    float get_best_x() const { return global_best_pos[0]; }
    float get_best_y() const { return global_best_pos[1]; }
    float get_best_score() const { return global_best; }

private:
    const Terrain& terrain_;
    float default_v_max_;
    int num_particles_ = 0;

    // Converted to std::array for Pybind11 compatibility, mimicking your vector<vector>
    std::vector<std::array<float, 2>> vel;     // {vx,vy}
    std::vector<std::array<float, 2>> pos;     // {x,y}
    std::vector<std::array<float, 2>> bestpos;
    std::vector<float> perbest;

    float global_best = -1e9f;
    std::array<float, 2> global_best_pos = {0.0f, 0.0f};
    
    // gridsize = {x_min, x_max, y_min, y_max} (Set to Pygame bounds)
    std::vector<float> gridsize = {-800.0f, 800.0f, -600.0f, 600.0f}; 

    mutable std::random_device rd;
    mutable std::mt19937 gen;

    // function to optimize
    float f(float x, float y) const;
};