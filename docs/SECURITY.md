# Security Design

## Controls

### Least privilege
Every API endpoint declares one or more permitted local roles. The UI is not trusted as a security boundary; authorization occurs server-side.

### Authentication
Local username/password authentication uses Argon2 password hashing. JWT access tokens are short-lived. Administrative and QC accounts should additionally use hardware-backed MFA at the workstation or OS layer before production deployment.

### Account lockout
Repeated failed logins increment a counter. Once the configured threshold is reached, the account is temporarily locked and the event is audited.

### Audit
Sensitive events are appended to `audit_logs`. Each record includes the hash of the previous record and its own SHA-256 hash. This provides tamper-evidence within the database.

For validated production deployment, copy audit events to a separate append-only/WORM-controlled store and restrict database deletion privileges.

### Encryption
The MVP supports encrypted backups. Production should use:

- full-disk encryption on every host
- encrypted removable backup media
- TLS for LAN traffic
- database encryption appropriate to the chosen database
- controlled key custody and rotation

### Network
The operational environment should use an air-gapped or tightly firewalled LAN. No public inbound service should be exposed.

### Data minimisation
Customer records use an internal reference and display label rather than collecting unnecessary personal information.

## Important production hardening

- Replace the development secret values.
- Disable direct database access for ordinary users.
- Use PostgreSQL with separate database roles.
- Implement row-level security where required.
- Place audit storage outside the ordinary application write path.
- Require dual approval for emergency access.
- Apply OS hardening and removable-media controls.
- Perform independent penetration testing and validation.
