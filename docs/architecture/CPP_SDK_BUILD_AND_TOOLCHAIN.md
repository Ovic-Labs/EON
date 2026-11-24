# OVIC EON — C++ SDK Build and Toolchain Specification

**Document ID:** `EON-SPEC-CPP-006`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Build Engineers, CI/CD Maintainers  
**Traceability:** `EON-ARCH-CPP-001`, ADR-020  

---

## 1. Supported Toolchains and Standards

- **Language Standard:** ISO C++17 (`-std=c++17`). Optional features guarded by `__cplusplus >= 202002L` (C++20).
- **Supported Compilers:**
  - GCC 11.4+, GCC 12+, GCC 13+ (Linux x86_64, aarch64)
  - Clang 14+, Clang 15+, Clang 16+ (Linux, macOS)
  - MSVC 2022 (v143 toolset, Windows 10/11)
- **Build System:** Modern CMake 3.22+ (`cmake_minimum_required(VERSION 3.22)`).
- **Robotics Middleware Integration:** `ament_cmake` package support for ROS 2 Humble and Jazzy (Legacy: Iron).

---

## 2. CMake Targets and Modern Export Conventions

The build system exports standard namespaced targets:
- `eon::sdk` (Dynamic shared library `libeonsdk.so`)
- `eon::sdk_static` (Static library `libeonsdk_static.a`)
- `eon::c_api` (Flat C ABI shared library `libeon_c.so`)

### Example Downstream `CMakeLists.txt`
```cmake
cmake_minimum_required(VERSION 3.22)
project(robot_social_node CXX)

find_package(eon REQUIRED CONFIG)

add_executable(robot_social_node src/main.cpp)
target_link_libraries(robot_social_node PRIVATE eon::sdk)
```
