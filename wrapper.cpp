#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "terrain.hpp"
#include "engine.hpp"

namespace py = pybind11;

PYBIND11_MODULE(pso_core,m) {
    py::class_<Terrain>(m,"Terrain")
        .def(py::init<float,float>())
        .def("set_target", &Terrain::set_target)
        .def("regenerate_decoys", &Terrain::regenerate_decoys)
        .def("fitness_at", &Terrain::fitness_at)
        .def("get_target_x", &Terrain::get_target_x)
        .def("get_target_y", &Terrain::get_target_y)
        .def("get_world_half", &Terrain::get_world_half);

    py::class_<PSOEngine>(m, "Swarm")
        .def(py::init<const Terrain&, int, float>(), py::keep_alive<1, 2>())
        .def("reset", static_cast<void (PSOEngine::*)()>(&PSOEngine::reset))
        .def("reset", static_cast<void (PSOEngine::*)(int)>(&PSOEngine::reset))
        .def("step", &PSOEngine::step)
        .def("get_pos", &PSOEngine::get_pos)
        .def("get_best_x", &PSOEngine::get_best_x)
        .def("get_best_y", &PSOEngine::get_best_y)
        .def("get_num_particles", &PSOEngine::get_num_particles);
}
