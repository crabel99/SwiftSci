# Replay the counter evidence

Use the recorded Python 3.14.6 interpreter and source checkout at `06adea701994f8fbbe82481684dfdafd77958a09`. Keep its controller files and the analyzer unchanged. The original audit also requires the recorded Swift executable, Python executable, native calibration library, and external reference inputs. This archive does not bundle those large inputs or the production executable.

1. Extract `experiment.tar.gz` into a new directory for inspection.
2. Verify its file bytes against `manifest.json` before modifying any output.
3. Read `method.json` and the source fingerprints to identify the recorded collection location and programs.
4. At the original collection location, run `verify-declared-smoke.py` with the recorded interpreter. The script replays the diagnostic analysis and checks every original capture file remains unchanged. PID absence is a fresh observation and can differ if an identifier is reused later.
5. To replay only the older capture as retrospective diagnostics, invoke `operating_state.py CAPTURE --output NEW_DIRECTORY`. This does not create a pre-run declaration for historical data.

The archive includes `run-declared-smoke.sh` as the exact acquisition recipe. Do not run it to replay saved data. Reusing its existing output directory fails intentionally. A new collection is a new experiment, with a new output directory and pre-run method.

`archive-integrity.json` records extraction and file-hash verification. `declared-smoke-verification.json` records the live source-dependent replay. These are different checks. Neither changes a quality-control failure into a pass.
