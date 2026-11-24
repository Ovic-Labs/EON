# OVIC EON — C++ SDK ABI Compatibility Specification

**Document ID:** `EON-SPEC-CPP-005`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Release Engineers, Systems Architects  
**Traceability:** `EON-ARCH-CPP-001`, ADR-020  

---

## 1. ABI Stability Mandate

In commercial robotics ecosystems, third-party developers, hardware vendors, and ROS 2 distribution maintainers build against shared libraries. ABI (Application Binary Interface) breaks force downstream consumers to recompile their entire software stacks.

To ensure long-term binary compatibility:
1. **Pimpl (Pointer to Implementation):** All public classes store state exclusively inside an opaque heap-allocated `Impl` pointer. The sizeof public classes remains constant across minor versions.
2. **C-ABI Bridge (`eon_c.h`):** For foreign function interfaces (FFI) such as Python `ctypes`, Rust FFI, and Go cgo, an explicit `extern "C"` flat ABI is exported with strict semantic versioning.
3. **Symbol Visibility Control:** All internal classes and functions are compiled with `-fvisibility=hidden`. Only explicitly annotated public symbols (`EON_SDK_API`) are exported in the dynamic symbol table.

---

## 2. Flat C-ABI Header (`eon_c.h`)

```c
#ifndef EON_C_API_H
#define EON_C_API_H

#include <stdint.h>
#include <stddef.h>

#if defined(_WIN32)
  #if defined(EON_SDK_EXPORTS)
    #define EON_SDK_API __declspec(dllexport)
  #else
    #define EON_SDK_API __declspec(dllimport)
  #endif
#else
  #define EON_SDK_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct eon_client_t eon_client_t;

typedef enum {
    EON_OK = 0,
    EON_ERR_NOT_CONNECTED = 1,
    EON_ERR_TIMEOUT = 2,
    EON_ERR_INVALID_ARG = 3,
    EON_ERR_INTERNAL = 4
} eon_status_t;

EON_SDK_API eon_status_t eon_client_create(const char* endpoint_uri, eon_client_t** out_client);
EON_SDK_API eon_status_t eon_client_destroy(eon_client_t* client);
EON_SDK_API eon_status_t eon_client_connect(eon_client_t* client);
EON_SDK_API eon_status_t eon_client_disconnect(eon_client_t* client);

#ifdef __cplusplus
}
#endif

#endif // EON_C_API_H
```
