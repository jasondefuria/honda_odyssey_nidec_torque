# Offline validation sources

These scripts execute the preserved original firmware through a small SH-2A p-code interpreter. They never write the ROM and require the exact recorded SHA-256. Keep this folder next to `user.original.bin`.

Install `pypcode==4.0.0` in a Python virtual environment, then run an individual script with that environment's Python. Results go to this folder's `results/`, separate from the recorded JSON evidence. No vehicle, bus, flash programmer, network connection or ECU is used.

The three `exhaustive_*.py` scripts cover all signed/raw 16-bit inputs in their stated dimensions and can take several minutes. Curve and monitor scripts support `--resume` from their own saved progress; omit it for a fresh complete run. Directed `verify_*.py` scripts run quickly. Read each script and report for its assumptions and substitutions.

The harness is a research execution model, not a validated hardware emulator. Unsupported operations and out-of-range writes fail. Test success does not establish physical torque, real-time behavior, complete flash acceptance or suitability of a modified firmware image.

The recorded main/monitor runs initially used an ideal interpolation oracle, exposed a one-count discrepancy, and were completed using the corrected split fixed-point oracle included here. Original banks 1–3 were retained on resume; their valid output hashes match the corrected model. The initial logs are retained in the working directory.
