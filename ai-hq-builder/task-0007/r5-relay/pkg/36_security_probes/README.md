# ChatGPT Independent R4 Probe Evidence

These files support `36_ChatGPT_Concurrency_Reverification_R4.md`.

The controlling concurrency test is `chatgpt_r4_prelock_probe.py`, not the Builder's client-side pre-send barrier. The gate-blocking regression is `chatgpt_capture_publication_fault_probe.py`.

All scripts are standard-library Python. Pass the target `stub_server.py` path as the first argument. `chatgpt_r4_revoke_epoch_probe.py` and `chatgpt_r4_nway_probe.py` import `chatgpt_r4_prelock_probe.py` from this same directory.

Random IDs and timestamps will differ on rerun. Compare status, outcome, cardinality, final state, evidence presence, and quota—not raw bytes.
