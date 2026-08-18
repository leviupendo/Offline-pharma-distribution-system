# Architecture Decisions

## ADR-001 Local-first
Operational records remain on site. No cloud service is required.

## ADR-002 Relational database
A relational model supports transactional inventory, orders, traceability and integrity constraints.

## ADR-003 RBAC
Permissions are tied to local roles rather than individual ad-hoc grants.

## ADR-004 Append-only audit chain
Each audit entry includes the previous entry hash, making unauthorized modification detectable.

## ADR-005 Device adapters
Scanners, scales, printers and sensors integrate through local adapters so hardware cannot bypass business rules.

## ADR-006 Controlled exports
Exports must be explicit, authorized and logged. Anonymous aggregate export can be enabled only under an approved procedure.
