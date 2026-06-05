# Update Manifest

Current project memory manifest for future Codex threads.

Check these files first:
- AGENTS.md
- README.md
- docs/project-context.md
- docs/current-scope.md
- docs/api-contracts.md
- docs/workflows.md
- docs/data-model.md
- docs/architecture.md
- docs/security.md
- docs/decisions.md
- docs/helpdesk-abstraction.md
- examples/oms-search-orders-response.json
- examples/oms-search-orders-response-expanded-sanitized.json
- examples/oms-get-order-details-response-not-expanded-sanitized.json
- examples/oms-get-order-details-response-expanded-sanitized.json

Current implemented capabilities:
- Render Web Service deployment
- production hardening with `APP_ENV=production`
- inbound `X-API-Key` auth
- Order Business API real client
- Freshdesk private-note adapter
- `POST /freshdesk/recent-orders`
- Sales Order link in Freshdesk note
- exact contact match before partial fallback
- phone-only/email-only fallback for partial contact matches
- human-friendly order date, ETA window, and first scan time formatting

Required OMS keywords:
- filter_mode=all|any
- expand=true
- orders[].details
- tracking_status
- tracking_status_urls fallback

Current production safety keywords:
- INBOUND_API_KEY
- DRY_RUN
- EXPOSE_DOCS=false
- EXPOSE_DEBUG_ERRORS=false
- /health
