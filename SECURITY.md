# Security Policy

## Supported versions

Security fixes are provided for the latest released minor version. Users should
upgrade to the newest release before reporting an issue.

| Version | Supported |
| --- | --- |
| 0.2.x | Yes |
| Earlier versions | No |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's
**Report a vulnerability** flow in the Security tab of this repository. Include:

- affected version and component;
- reproduction steps or a minimal proof of concept;
- impact and realistic attack conditions;
- suggested remediation, if known.

Please avoid accessing data that is not yours, disrupting services, or publicly
disclosing the issue before a fix is available. Maintainers will acknowledge a
complete report as soon as practical and coordinate validation, remediation,
and disclosure.

Jarvis Core processes untrusted model and tool content. A bug is especially
important to report when it can cross trust boundaries, escape token/resource
limits, expose secrets, or alter evidence and verification records.
