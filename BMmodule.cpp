
#include <algorithm>
#include <cmath>
#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <array>
#include <complex>

namespace py = pybind11;

using arr_out = py::array_t<double>;
using namespace py::literals;

double gaussian_box_muller() {
    double x = 0.0;
    double y = 0.0;
    double euclid_sq = 0.0;

    // Continue generating two uniform random variables
    // until the square of their "euclidean distance"
    // is less than unity
    do {
        x = 2.0 * rand() / static_cast<double>(RAND_MAX) - 1;
        y = 2.0 * rand() / static_cast<double>(RAND_MAX) - 1;
        euclid_sq = x * x + y * y;
    } while (euclid_sq >= 1.0);

    return x * sqrt(-2 * log(euclid_sq) / euclid_sq);
}

arr_out BM(const int& n, const int& N, const double& S0, const double& T,
           const double& sigma, const double& mu, const double& r) {
    double dt = T / static_cast<double>(N);
    auto result = arr_out({n, N + 1});
    auto result_p = result.mutable_unchecked<2>();
    for (int k = 0; k < n; k++) {
        result_p(k, 0) = S0;
    }
    for (int i = 0; i < n; i++) {
        for (int j = 1; j < N + 1; j++) {
            double Z = gaussian_box_muller();
            result_p(i, j) = result_p(i, j - 1) * exp(mu * dt - sigma * sigma * dt / 2 + sigma * sqrt(dt) * Z);
        }
    }

    return result;
}

PYBIND11_MODULE(BMmodule, m) {
    m.doc() = "Matrix (n,N) where each row is a simulation of a GBM";
    m.def("BM", &BM, "Matrix (n,N) where each row is a simulation of a GBM");
}
