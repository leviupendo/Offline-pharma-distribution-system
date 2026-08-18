# Backup and Restore Runbook

## Backup
1. Set `BACKUP_KEY` in the environment to a real random secret. If it is
   unset, `scripts/backup.py` will still run but writes an **unencrypted**
   `.db` file and prints a warning — fine for local dev, not for anything
   containing real data.
2. Stop or quiesce writes if the database technology requires it.
3. Run `python scripts/backup.py`. With `BACKUP_KEY` set, this produces a
   `pharma-<timestamp>.db.enc` file plus a `.sha256` checksum, and a `.salt`
   file in the backup directory (not secret, but required to restore).
4. Verify the generated SHA-256 checksum.
5. Copy the encrypted backup **and the `.salt` file** to approved offline
   media. A backup without its salt file cannot be decrypted even with the
   correct `BACKUP_KEY`.
6. Record media identifier and storage location.

## Restore
1. Obtain authorization.
2. Isolate the restore environment.
3. With `BACKUP_KEY` set and the matching `.salt` file present alongside
   the backup, run `python scripts/restore.py <backup file> -o restored.db`.
   This verifies the checksum, decrypts, and writes the plaintext database.
4. Restore into a clean database environment.
5. Run schema/startup checks.
6. Run `python scripts/verify_audit.py`.
7. Perform UAT smoke tests.
8. Record restore evidence.
9. Do not overwrite production until the recovery decision is formally approved.
