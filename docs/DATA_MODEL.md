# Data Model

## Core entities

- Product
- Batch
- PacketProduction
- Inventory
- Customer
- Order
- OrderLine
- User
- AuditLog

## Traceability

`Product → Batch → PacketProduction → Inventory → OrderLine → Order`

This supports local traceability from bulk production through a packet lot and final order.

## Customer privacy

The MVP deliberately uses `customer_ref` as the operational identifier. Additional customer information should only be added where operationally and legally necessary.
