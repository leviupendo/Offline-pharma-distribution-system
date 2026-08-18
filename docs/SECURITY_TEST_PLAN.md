# Security Test Plan

## Authentication
- invalid password rejected
- locked account rejected
- disabled account rejected
- expired token rejected

## Authorization
- Order Entry cannot release a batch
- Production cannot approve QC
- Warehouse cannot modify customer master data
- Auditor cannot write operational data
- Guest cannot perform privileged actions

## Data integrity
- negative stock rejected
- unreleased batch cannot enter finished inventory
- rejected batch cannot enter finished inventory
- invalid order transitions rejected
- audit chain detects modification

## Privacy
- customer model uses internal reference
- no outbound HTTP client in core application
- no analytics/telemetry SDK
- backup files are handled locally

## Operational
- backup succeeds
- backup checksum verifies
- clean restore succeeds
- application starts without internet connectivity
