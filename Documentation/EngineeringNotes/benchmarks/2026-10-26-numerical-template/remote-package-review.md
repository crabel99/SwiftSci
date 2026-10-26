# Remote package evidence review

No open source or evidence-binding findings after the completed run. This review launched no build, numerical consumer or network request.

`check-remote-package.py` uses the unchanged public template manifest and fresh native build/package directories. The completed receipt names source `0e1635199654ac6a20b32ea53eea0ffdfa39e747`, records resolve/build/run exit codes of 0 and records exact JSON equality with `final-run-qualified/prepared.json`. It binds its controller, manifest, consumer, logs, binary and result by SHA256. Its checkout proof includes all tracked Sources files and Package.swift; qualification independently checks completeness, actual hashes, exact HEAD, clean checkout and equality with the qualified local source.

SwiftPM's checkout origin points to its local repository mirror. That is expected, but it does not itself identify the remote URL. Qualification follows the mirror origin to `https://github.com/crabel99/SwiftSci.git`, checks the resolved SwiftSci pin's URL/revision, and verifies every resolved dependency checkout HEAD against the preserved Package.resolved pins. Resolve.log independently records the correct URL and exact source checkout. Qualification binds the resolved file's actual SHA alongside the original controller receipt without altering that receipt or controller after execution.

The native executable's recorded SHA matches the actual binary. All three recorded log hashes match their files, the build log reports success, and the result's actual hash and complete parsed JSON match the qualified prepared output. These checks extend the earlier local-manifest-substitution proof to actual remote package consumption. The local proof and historical audits remain retained.

This is one successful package run on the recorded host/toolchain. It establishes no cross-platform, statistical-quality, performance, memory-bound or security guarantee. Published records omit checkouts, build caches and binaries; their hashes remain in the evidence. Replaying original qualification needs those retained local artifacts, while publication verification checks the standalone record manifest and transformations.
