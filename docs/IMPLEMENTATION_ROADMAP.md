# Implementation Roadmap

## Completed in v0.2

- [x] Local authentication
- [x] RBAC
- [x] Login lockout
- [x] Batch lifecycle
- [x] QC decision
- [x] Packaging records
- [x] Reject reconciliation
- [x] Inventory movements
- [x] FEFO allocation
- [x] Order lifecycle
- [x] Proof of delivery
- [x] Audit hash chain
- [x] Dashboard
- [x] Expiry report
- [x] Encrypted development backup
- [x] Docker foundation
- [x] GitHub Actions tests
- [x] Threat/security/operations documentation

## v0.3 — hardening

- [ ] Alembic migrations
- [ ] PostgreSQL production schema
- [ ] PostgreSQL roles and permissions
- [ ] Row-level security where required
- [ ] TLS certificate management
- [ ] CSRF/session hardening if cookie auth is introduced
- [ ] Rate limiting
- [ ] Password reset/offline administrator recovery
- [ ] MFA integration
- [ ] Dual-control emergency access
- [ ] Audit export to append-only/WORM store
- [ ] Key management and rotation

## v0.4 — warehouse/device operations

- [ ] Barcode scanning
- [ ] GS1-compatible identifier model where applicable
- [ ] Label templates
- [ ] Printer adapter
- [ ] Scale adapter
- [ ] Temperature sensor adapter
- [ ] Stock count workflow
- [ ] Cycle counting
- [ ] Stock transfer
- [ ] Quarantine locations
- [ ] Returns
- [ ] Recall workflow

## v0.5 — quality and validation

- [ ] QC test catalogue
- [ ] QC sample records
- [ ] Electronic approvals/signatures
- [ ] Batch genealogy
- [ ] Packaging reconciliation
- [ ] Deviation/CAPA records
- [ ] Change control
- [ ] Document control
- [ ] Validation protocol
- [ ] Validation report
- [ ] Backup/restore qualification
- [ ] Disaster-recovery test

## v1.0 — controlled production candidate

The v1.0 gate should require:

- security review
- threat model review
- independent testing
- database recovery test
- offline update test
- audit integrity test
- role-separation test
- user acceptance testing
- SOP approval
- infrastructure qualification
- applicable regulatory/data-integrity review
- documented release approval
