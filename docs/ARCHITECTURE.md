# Architecture

## Deployment modes

### Single-server
One hardened local server runs FastAPI and PostgreSQL. Workstations access the application over the private LAN.

### Desktop
A controlled local workstation can run the application and database for small deployments.

## Data flow

1. Production creates a batch in quarantine.
2. QC records release or rejection.
3. Production records packet production from the released batch.
4. Warehouse receives packet lots into finished inventory.
5. Order Entry creates an order using an internal customer reference.
6. Warehouse allocates released inventory using FEFO.
7. Warehouse progresses pick/pack/ship/deliver statuses.
8. Audit records are generated at every sensitive transition.

## Tons → packets

The conversion is:

`packets = floor((tons × 1,000,000) / fill_weight_grams)`

The production record should also capture actual yield, rejected packets and reconciliation losses before a validated production deployment.

## Device integration

The architecture intentionally isolates peripherals behind local adapters:

- barcode scanner → keyboard/USB serial adapter
- label printer → local print driver
- scale → approved local serial/USB integration
- temperature sensor → local sensor service

No device should require a cloud service for operational use.
