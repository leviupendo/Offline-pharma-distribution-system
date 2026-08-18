# Device Integration Plan

The application keeps physical device access behind local adapters. Device code must never be allowed to bypass business rules.

## Barcode scanners
Use keyboard-emulation or a local serial adapter. Validate the scanned identifier against the local product/lot registry before accepting it.

## Label printers
A local print service should receive a validated label payload containing only approved fields.

## Scales
A scale adapter should capture:
- reading
- unit
- timestamp
- device identifier
- operator
- transaction reference

Measurements used for regulated records require appropriate calibration and validation procedures.

## Temperature sensors
Record:
- sensor ID
- location
- timestamp
- reading
- unit
- alarm state

The application should locally queue sensor records if a device temporarily disconnects.

## Offline rule
No device adapter may silently upload readings to the internet.
