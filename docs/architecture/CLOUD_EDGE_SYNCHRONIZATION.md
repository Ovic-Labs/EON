# OVIC EON — Cloud-Edge Synchronization Specification

**Document ID:** `EON-SPEC-CLD-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Distributed Systems Engineers, Cloud Backend Developers  
**Traceability:** `EON-ARCH-CLD-001`, ADR-024  

---

## 1. Store-and-Forward Synchronization Protocol

Robotic fleets operate over unpredictable wireless networks (Wi-Fi, 4G/5G, satellite). The cloud sync agent on the edge uses an asynchronous, transactional store-and-forward queue:

```text
[EON Core Context Events] ---> [Local SQLite Sync Outbox]
                                        |
                             (Network Available?)
                             /                  \
                        [YES]                    [NO]
                          /                        \
                         v                          v
             [Stream Batch to Cloud]      [Retain in Outbox]
             [Receive Cloud ACK]          [Backoff & Retry]
             [Delete Outbox Record]
```

---

## 2. Conflict Resolution and CRDTs

When multiple robots interact with the same user across different facilities (e.g., patient in Hospital Room A and Room B):
1. **Conflict-Free Replicated Data Types (CRDTs):** Subject preferences (e.g., preferred interaction style, introverted pacing) are modeled as Observed-Remove Sets (OR-Sets) and Last-Write-Wins Registers (LWW-Register).
2. **Vector Clocks:** Every context update carries a vector clock tuple `(robot_id, sequence_number, timestamp_utc)`. In the event of conflicting concurrent updates, the cloud reconciliation engine applies causal ordering rules.
3. **Graceful Merge:** If a conflict cannot be deterministically resolved, the system retains both values as alternate context hypotheses rather than overwriting user data.
