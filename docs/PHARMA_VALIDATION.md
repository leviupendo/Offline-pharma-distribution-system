# Pharmaceutical Validation and Data Integrity

This document is a project checklist, not regulatory advice.

## Required controls before operational use

### Identity
- Unique account per person
- No shared administrator accounts
- Role assignment approved by management
- Timely offboarding

### Data integrity
The implementation should be assessed against the organization's applicable ALCOA+ expectations:

- attributable
- legible
- contemporaneous
- original
- accurate
- complete
- consistent
- enduring
- available

### Batch records
Each production batch should have controlled records for:

- source/material references
- production quantity
- dates
- equipment where applicable
- operator identity
- packaging output
- rejects
- reconciliation
- QC results
- disposition

### Audit trail
Audit records should capture:

- who
- what
- when
- before/after values where relevant
- reason for critical changes

Audit data must not be alterable by ordinary application users.

### Electronic approvals
Where electronic records/signatures are used, determine the applicable legal and regulatory requirements before implementation.

### Backup
- scheduled backup
- encrypted media
- controlled custody
- restore test
- documented retention
- separate offline copy

### Change control
Every production software change should have:

1. change request
2. risk assessment
3. development
4. testing
5. approval
6. controlled deployment
7. post-deployment verification

## Acceptance tests

- Unauthorized role cannot release a batch.
- Released inventory cannot be created from a rejected batch.
- FEFO does not allocate unreleased stock.
- Inventory cannot become negative.
- Order state transitions reject invalid paths.
- POD can only be recorded for shipped orders.
- Login failures are audited.
- Disabled users cannot authenticate.
- Audit hash chain detects modification.
- Backup can be restored on a clean environment.
