from pathlib import Path
import argparse, hashlib, json, os, re, shlex, shutil, subprocess, sys, time

parser = argparse.ArgumentParser(
    description="Run SwiftSci workflow checks locally with explicit toolchain parity."
)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--swift-version", required=True, help="Swift version used by CI")
parser.add_argument("--xcode-version", help="Xcode version used by CI; required for the full run")
parser.add_argument("--sdk-version", required=True)
parser.add_argument("--codeql", type=Path)
parser.add_argument(
    "--codeql-version", help="CodeQL version used by CI; required for security checks"
)
parser.add_argument(
    "--jobs",
    choices=["main", "benchmarks", "mlx", "security", "security-python", "all"],
    default="all",
)
args = parser.parse_args()
root = args.root.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)


def capture(command):
    return subprocess.check_output(command, text=True, cwd=root).strip()


def workflow(name):
    return json.loads(
        capture(
            [
                "ruby",
                "-ryaml",
                "-rjson",
                "-e",
                "print JSON.generate(YAML.load_file(ARGV[0]))",
                str(root / ".github/workflows" / name),
            ]
        )
    )


swift = capture(["swift", "--version"])
version = re.search(r"Swift version (\d+\.\d+(?:\.\d+)?)", swift).group(1)
if version != args.swift_version:
    sys.exit(f"Compiler mismatch: expected {args.swift_version}, got {version}")
if sys.version_info[:2] != (3, 13):
    sys.exit("Python 3.13 is required, matching benchmark CI")
sdk = Path(os.environ["SDKROOT"])
sdk_version = json.loads((sdk / "SDKSettings.json").read_text())["Version"]
if sdk_version != args.sdk_version:
    sys.exit(f"SDK mismatch: expected {args.sdk_version}, got {sdk_version}")
xcode = capture(["xcodebuild", "-version"])
if args.jobs in ["all", "main", "benchmarks", "security"]:
    if not args.xcode_version or not xcode.startswith("Xcode " + args.xcode_version + "\n"):
        sys.exit("Select CI's matching Xcode and pass --xcode-version before running these checks")
    developer = Path(capture(["xcrun", "--find", "xcodebuild"])).resolve().parents[2]
    if not Path(shutil.which("swift")).resolve().is_relative_to(
        developer
    ) or not sdk.resolve().is_relative_to(developer):
        sys.exit(
            "Use the Swift compiler and SDK bundled with the selected Xcode; mixed toolsets are not accepted"
        )
codeql_version = None
if args.jobs in ["all", "security", "security-python"]:
    if not args.codeql or not args.codeql.is_file() or not args.codeql_version:
        sys.exit("CodeQL executable and expected version are required for security checks")
    codeql_version = json.loads(capture([str(args.codeql), "version", "--format=json"]))
    if codeql_version["version"] != args.codeql_version:
        sys.exit("CodeQL version does not match CI")
env = dict(os.environ, MACOSX_DEPLOYMENT_TARGET="14.0", SWIFTSCI_CI_OUTPUT=str(out))
state = {
    "scope": args.jobs,
    "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "xcode": xcode,
    "codeql": codeql_version,
    "swift": swift,
    "swift_path": capture(["which", "swift"]),
    "python": sys.version,
    "sdk": str(sdk),
    "sdk_version": sdk_version,
    "commit": capture(["git", "rev-parse", "HEAD"]),
    "workflows": {},
    "steps": [],
}
for name in ["ci.yml", "benchmark-conformance.yml", "codeql.yml"]:
    p = root / ".github/workflows" / name
    state["workflows"][name] = hashlib.sha256(p.read_bytes()).hexdigest()


def fingerprints():
    names = capture(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).split(
        "\0"
    )
    prefixes = (
        "Sources/",
        "Tests/",
        "scripts/",
        ".github/workflows/",
        "Benchmarks/Tools/",
        "Benchmarks/Python/",
        "Benchmarks/Tests/",
    )
    return {
        n: hashlib.sha256((root / n).read_bytes()).hexdigest()
        for n in sorted(set(names))
        if n
        and (n.startswith(prefixes) or n in ["Package.swift", "Package.resolved", ".codecov.yml"])
        and (root / n).is_file()
    }


state["source_fingerprints"] = fingerprints()
state["initial_git_status"] = capture(["git", "status", "--porcelain"])
if args.codeql and args.codeql.is_file():
    state["codeql_launcher_sha256"] = hashlib.sha256(args.codeql.read_bytes()).hexdigest()
report = out / (args.jobs + "-result.json")
if report.exists():
    sys.exit("This output already contains a run receipt; choose a fresh output directory")


def save():
    report.write_text(json.dumps(state, indent=2) + "\n")


save()


def run(label, body):
    index = len(state["steps"]) + 1
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    log = out / f"{args.jobs}-{index:02d}-{slug}.log"
    print("RUN", label, flush=True)
    start = time.time()
    with log.open("w") as stream:
        r = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", body],
            cwd=root,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    state["steps"].append(
        {
            "name": label,
            "command": body,
            "exit_code": r.returncode,
            "seconds": time.time() - start,
            "log": str(log),
            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        }
    )
    save()
    print("PASS" if r.returncode == 0 else "FAIL", label, flush=True)
    if r.returncode:
        sys.exit(r.returncode)


def run_steps(file, job, replace=None):
    for step in workflow(file)["jobs"][job]["steps"]:
        if "run" not in step:
            continue
        body = step["run"].replace("> coverage.lcov", '> "$SWIFTSCI_CI_OUTPUT/coverage.lcov"')
        if replace:
            body = replace(body)
        run(step.get("name", job), body)


if args.jobs in ["main", "all"]:
    for job in ["build", "build-release", "test", "docc-check"]:
        run_steps("ci.yml", job)
    # CI's historical export masks errors with `|| true`; local validation requires real source records.
    run(
        "Validate coverage export",
        'test -s "$SWIFTSCI_CI_OUTPUT/coverage.lcov"\nrg -q \'^SF:.*Sources/SwiftDataFrame/\' "$SWIFTSCI_CI_OUTPUT/coverage.lcov"',
    )
if args.jobs in ["benchmarks", "all"]:
    cache = Path('/private/tmp/swiftsci-library-integration-20261026/ci-bench-cache/standardized')
    worker = cache / "derived/Build/Products/Release/SwiftSciBenchmarkWorker"

    def paths(body):
        body = body.replace(
            "$HOME/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker",
            str(worker),
        )
        body = body.replace(
            "Benchmarks/Tools/bench.py build",
            "Benchmarks/Tools/bench.py build --cache "
            + shlex.quote(str(cache))
            + " --packages "
            + shlex.quote(str(Path('/private/tmp/swiftsci-library-integration-20261026/ci-bench-cache/packages'))),
        )
        body = body.replace("Benchmarks/Runs/ci-comparison", "${SWIFTSCI_CI_OUTPUT}/ci-comparison")
        for directory in ["ci-preflight-controls", "ci-acceptance", "ci-workflow-controls"]:
            body = body.replace(
                "Benchmarks/Runs/" + directory, '"${SWIFTSCI_CI_OUTPUT}/' + directory + '"'
            )
        return body

    run_steps("benchmark-conformance.yml", "verify", paths)
if args.jobs in ["benchmarks", "mlx", "all"]:
    mlx = workflow("benchmark-conformance.yml")["jobs"]["mlx"]
    for profile in mlx["strategy"]["matrix"]["profile"]:
        for step in mlx["steps"]:
            if "run" in step:
                run(
                    profile + ": " + step["name"],
                    step["run"]
                    .replace("${{ matrix.profile }}", profile)
                    .replace("Benchmarks/Runs/ci-mlx", "${SWIFTSCI_CI_OUTPUT}/ci-mlx"),
                )
if args.jobs in ["security", "security-python", "all"]:
    codeql = shlex.quote(str(args.codeql))
    for language in (["python"] if args.jobs == "security-python" else ["swift", "python"]):
        database = out / ("codeql-" + language)
        result = out / (language + ".sarif")
        command = f"{codeql} database create {shlex.quote(str(database))} --language={language} --source-root={shlex.quote(str(root))}"
        if language == "swift":
            command += " --command=" + shlex.quote(
                "swift build --arch arm64 --scratch-path " + shlex.quote(str(out / "codeql-build"))
            )
        else:
            command += " --build-mode=none"
        run("CodeQL " + language + " database", command)
        run(
            "CodeQL " + language + " analysis",
            f"{codeql} database analyze {shlex.quote(str(database))} codeql/{language}-queries:codeql-suites/{language}-code-scanning.qls --format=sarifv2.1.0 --output={shlex.quote(str(result))}",
        )
        data = json.loads(result.read_text())
        errors = [
            x
            for r in data["runs"]
            for x in r.get("invocations", [])
            if not x.get("executionSuccessful", True)
        ]
        if errors:
            sys.exit("CodeQL reported an unsuccessful analysis")
        state.setdefault("security_findings", {})[language] = sum(
            len(r.get("results", [])) for r in data["runs"]
        )
        save()
if fingerprints() != state["source_fingerprints"]:
    sys.exit("Source changed during local validation")
state["final_git_status"] = capture(["git", "status", "--porcelain"])
state["status"] = "passed"
save()
print("All requested local workflow checks passed", flush=True)
