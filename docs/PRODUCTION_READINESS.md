# Production Readiness Gate

This project is an application implementation baseline, not a declaration of regulatory compliance.

## Gate 1 — Infrastructure
- [ ] Dedicated server/workstation
- [ ] Full-disk encryption
- [ ] BIOS/UEFI password and boot restrictions
- [ ] Firewall denies unnecessary inbound/outbound traffic
- [ ] No public cloud dependency
- [ ] Controlled removable media
- [ ] Physical access register

## Gate 2 — Identity
- [ ] Unique account per person
- [ ] Strong password policy
- [ ] MFA for privileged roles where supported
- [ ] Automatic session lock
- [ ] Joiner/mover/leaver procedure
- [ ] Periodic access review

## Gate 3 — Data integrity
- [ ] Database backup schedule approved
- [ ] Restore test passed
- [ ] Audit chain verification passed
- [ ] Time source controlled
- [ ] Change control active
- [ ] Production database protected from direct user modification

## Gate 4 — Application validation
- [ ] Requirements traceability matrix
- [ ] Installation qualification
- [ ] Operational qualification
- [ ] Performance/user qualification
- [ ] UAT signed
- [ ] Security test evidence
- [ ] Failure/recovery test evidence

## Gate 5 — Operations
- [ ] SOPs approved
- [ ] Incident management
- [ ] Backup/restore SOP
- [ ] Emergency access SOP
- [ ] Recall SOP
- [ ] Deviation/CAPA process
- [ ] Periodic review

Only after the responsible organization signs the applicable evidence should the system be considered for production use.
