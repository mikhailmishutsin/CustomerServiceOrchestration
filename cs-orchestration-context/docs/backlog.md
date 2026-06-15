# Backlog

This file captures future improvements, refactors, and cleanup ideas that are worth keeping visible but are not urgent enough to block current delivery.

## Refactoring

### Simplify OMS order link construction

Current code includes a defensive helper that normalizes `ORDER_MANAGEMENT_BASE_URL` into the expected OMS order format:

```text
https://ds.utires.com/order_management/#order=<order_reference>
```

Why it exists:
- in deployment/configuration, the `#order=` fragment can be lost or entered incorrectly
- Freshdesk notes depend on the final link being exact

Why to revisit later:
- the OMS order URL format is standardized and known
- long-term, we may want to keep config strict and validation simple instead of repairing many possible malformed URL variants in code

Future refactor direction:
- validate `ORDER_MANAGEMENT_BASE_URL` early at config load time
- prefer one canonical configured value
- reduce or remove multi-branch normalization logic in the workflow once deployment config is stable
