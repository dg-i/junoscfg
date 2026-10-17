## REMOVED Requirements

### Requirement: Set validation reads every verb conversion reads

**Reason**: Moved to `validation/raw-set-input`, which holds what raw set input takes, with the
device's verb rule (probe D5 and A2) and the owner rule that set input is what a device
exports (decision 2026-10-17-set-input-is-a-device-export).
**Migration**: None; `validation/raw-set-input` keeps its scenarios and tests.
