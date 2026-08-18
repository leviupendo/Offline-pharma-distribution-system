# Offline Pharmaceutical Distribution System
A local-first "pharmaceutical" production, packaging, warehouse and distribution platform designed for controlled environments where operational data must remain on site.
Pharmaceutical is in qoutes as we arent talking about pharmarcies here!Depends on the drugs we are talking about!ha!

## Scope

- Local authentication and RBAC
- Production batches
- QC release/rejection
- Bulk-to-unit packaging records
- Finished-goods inventory
- FEFO allocation
- Customer-reference privacy
- Order fulfilment
- Proof of delivery
- Recall workflow
- Immutable/hash-chained audit trail
- Local encrypted backup workflow
- Change-control event recording
- Security and validation documentation
- Local hardware integration architecture

## Architecture

```text
Workstations
    |
Private LAN
    |
Local Application
    |
Relational Database ---- Append-only Audit
    |
Encrypted Backup Media

No cloud dependency
No required internet connection
No external identity provider
```

## Development

See `VSCODE_SETUP.md`.

## Production

Read `docs/PRODUCTION_READINESS.md` before any real deployment.

## Regulatory status

This repository is **not** a regulatory approval or compliance certification. The responsible organization must validate the system against its applicable requirements and approved procedures.
