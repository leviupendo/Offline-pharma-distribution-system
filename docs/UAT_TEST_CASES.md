# User Acceptance Test Cases

## UAT-001 Login
**Expected:** valid local user receives a session; invalid credentials are rejected and audited.

## UAT-002 RBAC
**Expected:** each role can perform only approved actions.

## UAT-003 Batch release
**Expected:** QC role can release/reject; non-QC role cannot.

## UAT-004 Packaging
**Expected:** bulk quantity produces a controlled packet count and records yield/reconciliation.

## UAT-005 Inventory
**Expected:** only released stock is available for fulfilment.

## UAT-006 FEFO
**Expected:** earliest valid expiry stock is allocated first.

## UAT-007 Order fulfilment
**Expected:** pick/pack/shipping actions create audit events and reduce inventory correctly.

## UAT-008 Recall
**Expected:** authorized recall changes batch status and exposes remaining inventory impact.

## UAT-009 Audit integrity
**Expected:** audit-chain verification succeeds; intentional modification is detected.

## UAT-010 Backup/restore
**Expected:** backup is created, checksum matches, and restore produces a usable database.

## UAT-011 Offline operation
**Expected:** application remains functional with internet physically disconnected.

## UAT-012 Recovery
**Expected:** documented recovery procedure restores the service from an approved backup.
