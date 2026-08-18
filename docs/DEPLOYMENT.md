# Offline Deployment

## Reference topology

```text
[Locked server room]
      |
      +-- Application server
      +-- PostgreSQL
      +-- Encrypted backup media
      |
[Private LAN]
      |
      +-- QC workstation
      +-- Production workstation
      +-- Warehouse workstation
      +-- Order-entry workstation
```

## Production deployment checklist

- Set `APP_ENV=production` (or anything other than `development`) in
  the app's environment. The application refuses to start under a
  non-development `APP_ENV` if `JWT_SECRET` or `BACKUP_KEY` are still
  at their placeholder values — treat that refusal as a checklist item
  being enforced automatically, not as a bug to work around.
- Generate and set a real, random `JWT_SECRET` (e.g. `openssl rand -hex 32`).
- Generate and set a real, random `BACKUP_KEY` before relying on
  `scripts/backup.py` for anything containing real data — without it,
  backups are written unencrypted (with a warning).
- Disable unnecessary network interfaces.
- Block outbound internet traffic at the firewall.
- Disable inbound remote administration.
- Install OS security updates using an approved offline transfer process.
- Enable full-disk encryption.
- Restrict physical server access.
- Create unique local accounts.
- Configure PostgreSQL with least-privilege roles.
- Enable LAN TLS.
- Configure encrypted backups.
- Test restoration.
- Configure time synchronization from an approved local source.
- Restrict removable media.
- Record hardware and software versions.
- Establish change control.

## Important

Docker is convenient for development. A production air-gapped environment should have a controlled image-transfer and verification process; do not configure the production host to pull images directly from public registries.
