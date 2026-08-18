# Operations

## Start

```bash
docker compose up -d
```

## Stop

```bash
docker compose down
```

## Backup

For the SQLite development deployment:

```bash
python scripts/backup.py
```

Production backup should use database-native PostgreSQL backups plus encrypted offline media and a documented restore test.

## Restore testing

A backup is not considered reliable until a restore has been performed on a clean machine and the restored application passes the site's acceptance checks.

## Emergency access

1. Identify the operational need.
2. Require two authorized people to approve break-glass access.
3. Record the reason before access where practical.
4. Grant the minimum temporary privilege.
5. Perform only the emergency task.
6. Remove the privilege immediately.
7. Review the audit record.
8. Document the incident and corrective action.

## Change control

Software updates must be:

- obtained from an approved source
- malware-scanned
- checksum/signature verified
- tested outside production
- approved before transfer into the air-gapped environment
