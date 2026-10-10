# q7m2-vx91-r4t8 — public isolated batch factory

This is the **public** side of Elysium's isolated artifact pipeline. Never copy private source, secrets, assets or control-plane files here. Deleting a commit or artifact after 24 hours cannot guarantee erasure of public copies or Git history.

## Workflow

The manually dispatched GitHub Actions workflow `Public Isolated Batch` runs Python unit tests, then packages up to 16 explicitly approved public jobs as deterministic ZIPs with SHA-256 digests in `dist/index.json`. Artifact retention: 1 day. PRs run tests but do not package submitted jobs.

Jobs must be stored as `jobs/JOB-ID/contract.json` and source files `modules/name.py`, `tests/test_name.py` relative to each job. Contract fields: `schema:1`, `job_id`, `validation_gate:"UNIT"`, `public_release_approved:true`, `integration_policy:"WINDOWS_VALIDATE_ONLY"`, and `files` with `path` and `sha256`. Paths and checksums are validated. No arbitrary script execution.

Run tests locally with `python -m unittest discover -s tests -p "test_*.py" -v`. Build with `python factory/package_batch.py --source jobs --output dist --limit 16`.

## Security and current limits

A contract's approval flag is **not cryptographic proof of authorization**. The private Windows receiver must independently verify an authenticated approval, GitHub artifact provenance, ZIP digest, exact contents, tests, and integration authorization. This public repository does not possess private credentials, execute supplied code, write to private GitHub or integrate into main. The workflow does not autonomously create new code; that requires a separate trusted worker and approved source package.
