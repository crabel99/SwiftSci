# Swift CodeQL finding triage

One finding remains open. Classification: confirmed use of weak cryptography in a retained legacy PostgreSQL authentication protocol, not introduced by the completion-metadata or cancellation changes. This is compatibility/security debt, not a clean-security result or a dismissed false positive.

## Artifact and source binding

- Reviewed source commit: `0e1635199654ac6a20b32ea53eea0ffdfa39e747`.
- SARIF: `ci-security-swift633-unsandboxed/swift.sarif`, SHA256 `1d29a8972bc2e0ff6cdb9dfa0616877915443b90891b3748c675524786599012`.
- Result receipt: `ci-security-swift633-unsandboxed/result.json`, SHA256 `d576f3531138041235df3aeed0c9110d5b6c7abc76e51c47bff5b3ae3d722ea8`. Its recorded SARIF SHA matches the actual file. Its source fingerprint for the flagged file matches the archived CodeQL source and Git objects below. Database and analysis log hashes also match the receipt.
- CodeQL 2.27.3 reports exactly one result, `swift/weak-password-hashing`, sink `Sources/SwiftDatabase/DatabaseConnection.swift:606`, password flow beginning at line619. The rule carries warning level and security-severity7.5. This is the tool's rule rating, not an independent exploitability assessment.
- `DatabaseConnection.swift` is 60,565 bytes with SHA256 `13cd5201a5d9b264de22fa09348199675441275ff2f47e41db62aabf400b012c` at baseline `c4de6cc866fff6f52100535dbcb38dd708558200`, final `0e1635199654ac6a20b32ea53eea0ffdfa39e747`, and original `0a2ab515b620c638bb15b525bf9851895fcfc33f`. The file in `database/src.zip` has that same hash.

The receipt's `status: passed` means extraction/analysis commands completed with exit0. Its `findings: 1` means security findings remain. The SARIF alone has no Git revision field; the receipt, source archive and matching hashes provide the binding.

## Call-site assessment

The private `pgMD5Password` helper is called only from the PostgreSQL startup authentication switch's case5 at lines489-494. The server has requested MD5 authentication; the client uses the supplied four-byte salt and sends a PasswordMessage. The helper computes the lowercase hexadecimal inner digest of password plus username, then the outer digest of that hex string plus salt, prefixed with `md5`. The flagged operation is this wire-response computation, not a newly added password-storage scheme.

That response matches PostgreSQL18's specified AuthenticationMD5Password exchange. Substituting SHA-256 within this helper would break the protocol. This protocol requirement explains the code; it does not make MD5 secure. [PostgreSQL18 protocol flow](https://www.postgresql.org/docs/18/protocol-flow.html#PROTOCOL-FLOW-START-UP).

PostgreSQL18 describes MD5 authentication as less secure, deprecates MD5-encrypted passwords, and directs installations toward SCRAM-SHA-256. It documents migration through SCRAM-compatible clients, password-encryption configuration, resetting stored passwords and authentication configuration. [PostgreSQL18 password authentication](https://www.postgresql.org/docs/18/auth-password.html).

## Remaining work

Preserve the SARIF and this finding. Track a separate PostgreSQL authentication policy change: decide whether to reject MD5 by default, require explicit legacy opt-in during deprecation, or remove support, with a documented compatibility impact. Validate the existing SCRAM branch and intended server/client migration using dedicated protocol and database tests before claiming it resolves deployment exposure. No such remediation or runtime validation occurred here.

This review changed no production source, ran no database test and makes no security guarantee. It establishes that the flagged code predates this change and explains why the legacy protocol uses MD5; it does not establish that retaining that protocol is acceptable for a particular deployment.
