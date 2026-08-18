# API Workflow Examples

## Login

`POST /api/auth/login`

```json
{
  "username": "admin",
  "password": "CHANGE_ME"
}
```

Use the returned bearer token for subsequent requests.

## Create product

`POST /api/products`

```json
{
  "code": "PRODUCT-001",
  "name": "Example Product",
  "packaging_type": "UNIT_DOSE_PACKET",
  "standard_fill_weight_grams": 1.0
}
```

## Create batch

`POST /api/batches`

A newly created batch enters `QUARANTINE`.

## QC release

`POST /api/batches/{id}/qc`

```json
{
  "decision": "RELEASED",
  "qc_results": "Approved according to validated QC procedure."
}
```

## Package

`POST /api/inventory/packaging?...`

Only released batches are accepted.

## Create order

`POST /api/orders`

```json
{
  "order_id": "ORD-001",
  "customer_ref": "CUST-001",
  "lines": [
    {"requested_quantity": 500}
  ]
}
```

## FEFO allocation

`POST /api/orders/{id}/allocate`

The server selects released inventory by earliest expiry.

## Order transitions

`POST /api/orders/{id}/status`

Valid sequence:

`ALLOCATED → PICKED → PACKED → SHIPPED → DELIVERED`

## Proof of delivery

`POST /api/orders/{id}/pod`

Only a shipped order can receive POD.
