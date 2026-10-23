# Library validation

Current inputs are in [examples/library/bl1.2](../../examples/library/bl1.2/README.md); see the repository [README](../../README.md) for Studio startup.

## Current scripts

| Script | Purpose |
| --- | --- |
| `scripts/run_business_logic_gates.py` | Generate a fresh Library prototype and run the full fake validation or the real smoke. |
| `scripts/test_run_business_logic_gates.py` | Test evidence isolation and matching fake-run prerequisites. |
| `scripts/observe_late_risk.py` | Read a selected prototype's SQLite database and invocation log without invoking AI or writing data. |
| `scripts/test_observe_late_risk.py` | Test observation semantics using temporary databases and logs. |

These are the only retained scripts. They use the Python standard library on the host; the runner also uses Docker Compose, the repository's generator and backend gates, and the frontend's installed Node tooling. The local `.gitignore` excludes Python caches.

## Run validation

From the Studio repository root, Python 3.9+ can run the seven helper tests without Docker or provider credentials:

```bash
python3 -B -m unittest discover -s docs/evidence/scripts -p 'test_*.py' -v
```

For full validation, start Docker services and install the frontend dependencies first:

The delivery default is real mode (`AI_RUNTIME_FAKE=0`), but `--mode fake` explicitly selects fake mode for generation and backend checks without changing that default or using provider credentials. Keep the local `config/secrets.env` file present for Compose; empty values are sufficient for fake validation. A real smoke requires your own valid keys.

```bash
python3 docs/evidence/scripts/run_business_logic_gates.py \
  --metadata examples/library/bl1.2/metadata.json \
  --case-data examples/library/bl1.2/fixture.json \
  --mode fake --validation-scope full \
  --output docs/evidence/business_logic_v12/fake
```

The full run generates a fresh prototype, checks TypeScript and the frontend build, and runs the frontend tests and backend gates. For a real smoke, use the same command with `--mode real` and an output ending in `business_logic_v12/real`. It requires a matching passing fake run and makes five provider calls on the successful path. Outputs under `run_*/` and generated prototypes remain Git-ignored.

To inspect an existing prototype, pass its explicit directory to `python3 docs/evidence/scripts/observe_late_risk.py --prototype <prototype-directory>`. Use `--help` for record and invocation selection options. A stored database value alone does not prove that an AI assessment succeeded.

## Historical evidence

On 2026-10-23, 931 historical evidence file versions, including generated source snapshots, old runbooks and the step-7 risk prompt snapshot, were archived and verified with SHA-256. After verification, 930 files were removed from the engineering delivery; the remaining file was the previous version of this readme, which was replaced with the current validation notes. Existing archives were reused for 405 file versions; the remaining 526 are in `studio_history_delta_20261023.tar.gz`.

Archives are kept separately in the workspace's `evidence_archives/` directory, beside `studio/`. `studio_history_20261023_manifest.json` maps every original path to its archived file or tar member and records its size and SHA-256. The manifest and new archive each have a `.sha256` sidecar. Restore into a separate directory and verify hashes before reusing historical evidence.

The 47 historical `step*` and `t*` scripts and 17 cached Python files were archived in `studio_legacy_scripts_20261023.tar.gz`, verified individually, then removed. `studio_legacy_scripts_20261023_manifest.json` records every original path, size, SHA-256 and archive member; both files have `.sha256` sidecars. The four current scripts were retained byte-for-byte. Historical scripts may require archived inputs or older services and are not current validation entry points.

The obsolete `_deferred/` shell verification script and the previous demo cheatsheet are in `studio_demo_deferred_20261023.tar.gz` with a `.sha256` sidecar. Runtime v1/v2 risk templates remain because registry and compatibility references still exist. Historical runs do not certify the current source revision.
