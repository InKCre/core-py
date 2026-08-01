# Security Policy

## Supported Versions

InKCre Core is pre-1.0 and does not currently publish supported release tags. Security
fixes target the current `main` branch and the canonical deployment built from it.

Older commits, forks, and independently modified deployments may still be assessed, but
the project does not promise patches or backports for them.

## Report A Vulnerability

Use GitHub's [private vulnerability reporting][report] for this repository. Do not open a
public issue, discussion, or pull request containing vulnerability details before the
report has been assessed.

Include enough evidence to distinguish a security boundary violation from a functional
bug or a hardening opportunity:

- affected revision and deployment shape;
- attacker capability and required preconditions;
- the asset or user interest that is harmed;
- the trust boundary that is crossed;
- minimal reproduction steps or a proof of concept;
- relevant, redacted logs or requests without live credentials or personal data.

If the issue affects another InKCre repository, use that repository's private reporting or
security policy when available. If it has no private channel, you may use this repository's
form and identify the affected repository. If you are unsure whether an issue is exploitable
or in scope, prefer a private report.

## What To Expect

Maintainers will assess reports on a best-effort basis and may ask for clarification or a
smaller reproduction. The project does not currently promise an acknowledgement or repair
SLA, operate a vulnerability reward program, or guarantee that every accepted report will
receive a CVE.

Please allow maintainers a reasonable opportunity to investigate and prepare a fix before
public disclosure. When a report is accepted, GitHub Security Advisories may be used for
private collaboration and coordinated publication.

## Security Model

The [Core Security Model](docs/30-unit-tdd/security-model.md) defines this repository's
actors, assets, trust boundaries, valid security harms, non-boundaries, and proportionality
method. It is the starting point for security-sensitive design and triage; implementation,
tests, CI, and deployment contracts remain authoritative for the controls they enforce.

[report]: https://github.com/InKCre/core-py/security/advisories/new
