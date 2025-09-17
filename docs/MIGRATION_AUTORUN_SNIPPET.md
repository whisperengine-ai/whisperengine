# Optional Automatic Migration Execution

If you want the application to automatically run pending migrations on startup, you can add this guarded snippet near early initialization (e.g. in `run.py` after environment load but before services start):

```python
# run.py (excerpt)
from env_manager import load_environment
load_environment()

import os, subprocess, sys

def run_pending_migrations():
    if os.getenv("RUN_DB_MIGRATIONS_ON_START") == "true":
        print("[startup] Running pending database migrations...")
        try:
            subprocess.run(
                [sys.executable, "scripts/db/run_migrations.py"], check=True
            )
            print("[startup] Migrations complete.")
        except subprocess.CalledProcessError as e:
            print(f"[startup] Migration failure: {e}. Aborting startup for safety.")
            sys.exit(1)

run_pending_migrations()
```

Then set in your environment:
```
RUN_DB_MIGRATIONS_ON_START=true
```

## Safety Notes
- Recommended only for controlled environments (dev, staging, internal).
- For production, prefer manual invocation + review: 
  ```bash
  python scripts/db/run_migrations.py --status
  python scripts/db/run_migrations.py
  ```
- If a migration fails, the script will exit non-zero and you can prevent partial startup.

## Rollback Strategy
This lightweight system does not auto-rollback. Always do a backup first:
```bash
./scripts/db/backup_all.sh
```

To revert: restore the Postgres dump you just created.

## Future Idea
Add `REQUIRE_LATEST_SCHEMA=true` to make the app refuse to start unless no pending migrations remain.
