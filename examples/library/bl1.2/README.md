# Library BL-1.2

A reproducible Studio example with a shared loan period, per-book returns, checkout-time risk assessment, and a three-step reading plan.

| File | Used by | Purpose |
| --- | --- | --- |
| `project.json` | Studio → Projects → upload | Import the class diagram and both interfaces. Its identities are separate from the earlier Library example. |
| `metadata.json` | The generator and validation runner's `--metadata` option | Supply the resolved generation input corresponding to the project. It is not a Projects upload file. |
| `fixture.json` | The validation runner's `--case-data` option | Supply fixed dates, synthetic history and expected facts for repeatable tests. It is not the date to enter during a live checkout. |
| `README.md` | Users and maintainers | Explain these inputs, their entry points and their limitations. |

Use the repository's normal `docker compose` commands to start Studio; see the [startup instructions](../../../README.md). These files are example inputs, not startup scripts. After importing the project, generate and run a prototype through Studio. No machine-specific launch script or external output directory is required.

Runtime configuration is ai_config 1.2 with `library_late_risk_v3`. The delivery defaults to real calls (`AI_RUNTIME_FAKE=0`): supply your own OpenAI and Groq keys via the ignored `config/secrets.env`. To use fixed demonstration responses instead, set `AI_RUNTIME_FAKE=1` locally and apply the environment change as described in [AI credentials and modes](../../../README.md#ai-credentials-and-modes). The automated fake tests select fake mode independently of this default. The generated applications and their databases are local outputs under `prototypes/generated_prototypes/`, not source files to commit.

## Validation

Use the current commands in [Library validation](../../../docs/evidence/readme.md). The runner consumes `metadata.json` and `fixture.json` directly; it does not import `project.json` through the Studio UI. A passing automated run therefore does not by itself verify the project-upload interaction. Optional real validation requires a matching passing fake run and makes five external model calls on the successful path.

Synthetic borrowing history demonstrates the integration mechanism, not calibrated predictive accuracy or an advantage over simple rules. Borrowed and returned books do not establish that the reader finished or liked them. Old shared-return databases are not automatically migrated. Model compatibility must be checked separately from the shared startup procedure.

## Maintaining the example

Keep these four files together. When the model changes, update the matching project and resolved metadata together, review the fixture's assumptions, then validate again. Keep generated applications, databases and logs out of this directory. Demo walkthroughs belong in `docs/demo/`.

When a new example replaces this version, validate it before archiving and removing the superseded inputs. The directory name identifies the supported example version; it does not provide a separate startup environment or guarantee compatibility with older generated databases.

## Integration check (2026-09-17)

Verified through Studio: project upload → Structure diagram → Generate Prototype → Run → librarian and member pages. The metadata saved by Studio exactly matches `metadata.json`. Full fake validation passed (38 backend groups, 13 frontend tests and build); the runner and read-only observation helper also passed 7 unit tests. The prototype service was checked with `AI_RUNTIME_FAKE=0`; this packaging check did not make new provider calls. Historical real-mode results are not presented as a new real smoke for this revision.
