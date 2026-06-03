# CustomerServiceOrchestration
Orchestration Layer for Customer Service department

## First milestone

This repo now includes the first small API skeleton for ticket enrichment:

- receives a normalized helpdesk ticket request
- reads sanitized mock OMS data
- normalizes recent order and shipment data
- prefers embedded `tracking_status` from `expand=true`
- returns a dry-run helpdesk update payload

## Local setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
```

Run the API locally:

```bash
python -m uvicorn cs_orchestration.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Current API

```text
POST /enrich-ticket
GET /health
```

`POST /enrich-ticket` currently uses mock OMS data from:

```text
cs-orchestration-context/examples/oms-search-orders-response.json
```
