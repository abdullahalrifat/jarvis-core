# Core certification evidence

Core release certification covers deterministic provider-neutral contracts, not the operating-system behavior of consuming applications.

Retain the exact release SHA, package version, Python matrix, formatter/lint/type/test/coverage results, wheel and sdist hashes, clean-environment installation results, metadata/provenance validation and consumer compatibility run URLs.

For inference transport changes, retain conformance results for:

- canonical URL normalization and bearer authentication;
- model catalog/capability response validation;
- chat and embedding payload compatibility;
- SSE decoding, malformed events and bounded response size;
- request IDs and normalized status/retryability errors;
- a timed-out request being issued once only;
- stream errors/cancellation closing the response and not silently replaying generation.

Jarvis and AI Stack must run their own consumer integration suites against the exact Core package version. Core does not itself certify model quality, backend cancellation, tenancy or host/container sandbox enforcement.
