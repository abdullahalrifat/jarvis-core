# World-class contract policy

Core is the semantic compatibility anchor for Jarvis, AI Stack and inference-facing clients.

Production deployments must:
1. pin an immutable Core release;
2. report component versions at startup/diagnostic time;
3. fail CI on unsupported Core drift;
4. retain the compatibility report with release evidence.

Core does not own provider credentials, network calls or OS isolation. Consumers remain responsible for enforcing those boundaries.
