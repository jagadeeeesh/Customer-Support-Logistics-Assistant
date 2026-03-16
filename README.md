# Automated Customer Support & Logistics Assistant 📦

This project implements a multi-action agent workflow for requests like:

> "Where is my order, and if it's delayed, can you give me a 10% discount code?"

The assistant runs a **reasoning loop** with four actions:

1. Query a SQL database for the customer's order by email.
2. Call an external shipping API (simulated HTTP service in this repo) for real-time status.
3. Evaluate business rules (delay + user asked for discount) and generate a 10% discount code when applicable.
4. Compose a final customer response with an LLM (Groq API), with a deterministic fallback template if LLM is unavailable.

## Architecture

- `app/database.py`: SQLite schema + seed data.
- `app/shipping_provider.py`: mock external shipping API over HTTP.
- `app/services.py`: repository, shipping client, business rules, discount generator, Groq LLM composer, and orchestrator.
- `app/api_server.py`: HTTP API exposing `/health` and `/support/request`.
- `app/main.py`: demo runner and server entrypoint.

## Run the End-to-End Demo

```bash
python -m app.main --mode demo --email alice@example.com \
  --customer-message "Where is my order, and if delayed can I get a 10% discount?" \
  --groq-api-key "$GROQ_API_KEY"
```

## Run as HTTP API

```bash
python -m app.main --mode serve --host 127.0.0.1 --port 8000 --groq-api-key "$GROQ_API_KEY"
```

Then in another terminal:

```bash
curl -X POST http://127.0.0.1:8000/support/request \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com", "customer_message":"Where is my order, and can I get a discount if delayed?"}'
```

## Seed Data

- `alice@example.com` → delayed scenario.
- `bob@example.com` → on-time scenario.

## Tests

```bash
pytest -q
```
