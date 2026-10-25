# Replay the frequency correlation

Use the recorded Python 3.14.6 interpreter for analysis. The standard library is sufficient. Use the installed R runtime to render the figure.

1. Extract `experiment.tar.gz` into a new directory.
2. Verify each file against `manifest.json` before changing any output.
3. Run the bound tests and raw replay from that directory.

```sh
/path/to/python3.14.6 run-verification.py
Rscript plot-correlation.R .
```

The replay runs the correlator in a temporary output directory and compares its four numeric output files with the archived copies. It checks bridge selection, all four selected offset cases, the rejected timestamp model, and partial-edge handling. `verification.json` records the interpreter, commands, input hashes, and test results. The three focused timestamp and overlap tests are separate from the complete replay test.

To regenerate the outputs explicitly:

```sh
/path/to/python3.14.6 correlate.py capture --output .
```

The archive includes the raw capture, direct clock bridge, fixed native program and source, analysis scripts, plot, source fingerprints, and saved review. No administrator access is needed for replay. Replay does not rerun the privileged profiler or the native workload. The reconstructed bridge producer is documentation of the described collection procedure, not the original command. Do not replace the historical bridge with a new observation.

Keep the raw capture unchanged. The `start_monotonic_ns` value from system Python 3.9 is not directly comparable with the C probe's absolute Mach timestamps. The analyzer uses the recorded clock bridge and checks it against the historical wall-time envelope. Four selected offsets are checked; a continuous uncertainty sweep is not claimed.
