#!/usr/bin/env python3
"""Keep our development records out of contribution-branch history."""
import subprocess
import sys

INTERNAL = (
    "ENGINEERING-NOTES.md",
    "Documentation/EngineeringNotes/",
    "Documentation/Research/",
    "Benchmarks/ARCHITECTURE.md",
    "Benchmarks/Results/StandardizedValidation/",
)
FORK_URLS = {
    "https://github.com/crabel99/SwiftSci",
    "git@github.com:crabel99/SwiftSci",
    "ssh://git@github.com/crabel99/SwiftSci",
}
NOTES_REF = "refs/heads/codex/engineering-notes"


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def check(revision):
    tip = git("rev-parse", "--verify", "--end-of-options", revision + "^{commit}")
    base = git("rev-parse", "--verify", "upstream/main^{commit}")
    paths = git("log", "--format=", "--name-only", base + ".." + tip).splitlines()
    blocked = sorted({p for p in paths if any(
        p.startswith(rule) if rule.endswith("/") else p == rule for rule in INTERNAL
    )})
    if blocked:
        raise ValueError("Internal development records found in outgoing history:\n" +
                         "\n".join(blocked) +
                         "\nKeep these on origin/codex/engineering-notes. A later deletion is insufficient.")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--check":
        check(sys.argv[2])
        print("PASS: contribution history contains no internal record paths")
        return
    if len(sys.argv) != 3:
        raise ValueError("Expected Git's remote name and URL, or --check REVISION")
    remote, url = sys.argv[1:]
    if url.endswith(".git"):
        url = url[:-4]
    for record in sys.stdin:
        local_ref, local_oid, remote_ref, remote_oid = record.split()
        if set(local_oid) == {"0"}:
            continue
        if remote_ref == NOTES_REF:
            if remote != "origin" or url not in FORK_URLS or local_ref != NOTES_REF:
                raise ValueError("The notes branch may only be pushed to its matching branch on our fork")
            continue
        check(local_oid)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print("PUSH BLOCKED: " + str(error), file=sys.stderr)
        sys.exit(1)
