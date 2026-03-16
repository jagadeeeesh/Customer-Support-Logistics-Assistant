# Automated Customer Support & Logistics Assistant 📦

This project implements a multi-action agent workflow for requests like:

> "Where is my order, and if it's delayed, can you give me a 10% discount code?"

The app runs a **reasoning loop** with four actions:

1. Query a SQL database for the customer's order by email.
2. Call an external shipping API (simulated HTTP service in this repo) for real-time status.
3. Evaluate business rules and generate a 10% discount code if the order is delayed beyond the guaranteed date.
4. Compose a final customer response containing logistics details and compensation when applicable.

## Architecture

- `app/database.py`: SQLite schema + seed data.
- `app/shipping_provider.py`: Mock external shipping API over HTTP.
- `app/services.py`: Repository, shipping client, business rules, discount generator, and orchestrator.
- `app/main.py`: End-to-end demo runner.

## Run the End-to-End Demo

```bash
python -m app.main
```

The script will:

- initialize the SQL database,
- start the simulated external shipping API,
- run the orchestrator flow,
- print the final composed customer response.

## Seed Data

- `alice@example.com` → delayed scenario (discount expected).
- `bob@example.com` → on-time scenario (no discount).

## Tests

```bash
pytest
```
