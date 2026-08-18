# Threat Model

| Threat | Control |
|---|---|
| Unauthorized workstation access | locked rooms, OS accounts, screen lock |
| Stolen password | strong passwords, lockout, MFA for privileged roles |
| Excessive privilege | RBAC and least privilege |
| Unauthorized batch release | QC-only release endpoint |
| Inventory manipulation | role checks + audit trail |
| Customer data leakage | minimal data + no automatic external integrations |
| Malicious USB | approved encrypted media only |
| Ransomware | offline encrypted backups + restore tests |
| Audit tampering | hash chaining + separate append-only storage |
| Remote intrusion | air-gapped/private LAN posture |
| Software supply-chain compromise | controlled offline update process |
| Insider misuse | separation of duties + audit review |

## Security boundary

The strongest boundary is the physical site plus the isolated network. The application must not be treated as the only security control.
