# Requirements Traceability Matrix

| Requirement | Implementation | Verification |
|---|---|---|
| Least privilege | RBAC dependencies | Security tests |
| Local authentication | `/api/auth/login` | Authentication tests |
| Lockout | failed-attempt counter | Login tests |
| Batch traceability | Batch + PacketProduction + Inventory | UAT |
| QC approval | batch QC workflow | Role tests |
| FEFO | inventory allocation | Inventory tests |
| Auditability | hash-chained AuditLog | `/api/validation/audit-integrity` |
| Backup | `scripts/backup.py` | Restore test |
| Recall | `/api/recalls` | Recall UAT |
| Change control | `/api/change-control` + audit | Change-control review |
| Offline operation | local-only architecture | Network isolation test |
| Minimal customer data | Customer reference model | Privacy review |
