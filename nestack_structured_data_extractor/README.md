# Nestack Structured Data Extractor

Backend-only API for extracting transaction fields from unstructured text with an LLM. Built with Python, Flask, and Gemini (`gemini-2.5-flash-lite`).

## Features

- `POST /extract` accepts `{"text": "..."}`.
- Returns seven fields: `vendor_name`, `amount`, `currency`, `date`, `category`, `description`, and `invoice_id`.
- Each field contains `value`, a per-field `confidence` from 0.0 to 1.0, and `needs_review`.
- `needs_review` is computed server-side as `confidence < 0.75`; top-level `review_required` is true if any field needs review.
- Missing values are always represented as `null`, with confidence capped at 0.20.
- Unknown transaction text and empty input produce a valid low-confidence schema rather than crashing.
- `GET /health` is provided for deployment health checks.

## Requirements

- Python 3.10+
- A Gemini API key from Google AI Studio

## Run locally

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your own `GEMINI_API_KEY`. Do not commit `.env` or expose your API key.

PowerShell environment variables can also be set for the current terminal:

```powershell
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
$env:GEMINI_MODEL="gemini-2.5-flash-lite"
python app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="YOUR_KEY_HERE"
export GEMINI_MODEL="gemini-2.5-flash-lite"
python app.py
```

The API runs at `http://127.0.0.1:8000`.

## Test the API

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"Paid ₹ 1,250 to AWS India Pvt Ltd on 12 March 2024. Invoice #INV-2024-0312. Services: cloud compute."}'
```

PowerShell equivalent:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/extract -ContentType 'application/json' -Body '{"text":"Paid ₹ 1,250 to AWS India Pvt Ltd on 12 March 2024. Invoice #INV-2024-0312. Services: cloud compute."}'
```

## How per-field confidence works

The prompt requests a separate confidence estimate for every field and defines confidence as the strength of the evidence for that particular value. It tells the model to score explicit and unambiguous evidence highly, use lower scores for inference, and return `null` with low confidence for missing or ambiguous data. It also warns the model not to assign one score to the whole response or copy the same score to every field. The server then validates the schema and applies the review threshold itself, rather than trusting the model to set `needs_review` correctly.

LLM-generated confidence is an estimate, not a statistically calibrated probability. The review flag is a workflow signal and should be validated against labeled examples before production use.

## Model choice

The assessment suggests Gemini 2.5 Flash-Lite. It is a lightweight model suitable for a small extraction API and supports JSON output mode. The model name is configurable with `GEMINI_MODEL`.

## Test all five assessment inputs

Start the API with a valid API key, then run:

```bash
python generate_results.py
```

This sends every entry in `sample_inputs.json` to the running `/extract` endpoint and writes the actual API responses to `results.json`. The generated array includes the sample label, input text, and response for traceability. Re-run it whenever you change the prompt or model. The included `results.json` currently contains provisional example responses so the expected shape is visible; it is **not evidence of a live LLM run**. Before submission, run this script with your own API key to replace it with real endpoint responses.

## Deployment

A Render blueprint is included in `render.yaml`; `Procfile` is also included for compatible platforms.

1. Create a **private** GitHub repository named `Advith_Nestack_Submission` (or the exact name requested by your assessment portal).
2. Push the code without `.env`, keys, or other secrets.
3. Deploy the repository as a Python web service. Build command: `pip install -r requirements.txt`; start command: `gunicorn app:app --bind 0.0.0.0:$PORT`.
4. Add `GEMINI_API_KEY` as a secret environment variable in the hosting dashboard. Set `GEMINI_MODEL` to `gemini-2.5-flash-lite`.
5. Confirm `/health` returns `{"status":"ok"}` and test `/extract` on the deployed URL.
6. Run `generate_results.py` against the deployed URL if you want `results.json` to contain deployed API responses: set `EXTRACTOR_BASE_URL` to the service base URL first.
7. Download/export the repository as a ZIP and submit the ZIP, live URL, and private repository access through the assessment portal.

For evaluation, add these collaborators to the private repository: `bishal@nestack.com`, `sannidhya@nestack.com`, and `sanjay@nestack.com`. Never make the repository public; the assessment says public repositories are disqualified.

## Response shape

```json
{
  "review_required": true,
  "fields": {
    "vendor_name": {"value": "AWS India Pvt Ltd", "confidence": 0.98, "needs_review": false},
    "amount": {"value": 1250, "confidence": 0.99, "needs_review": false},
    "currency": {"value": "INR", "confidence": 0.99, "needs_review": false},
    "date": {"value": "2024-03-12", "confidence": 0.99, "needs_review": false},
    "category": {"value": "software", "confidence": 0.81, "needs_review": false},
    "description": {"value": "Cloud compute services", "confidence": 0.91, "needs_review": false},
    "invoice_id": {"value": "INV-2024-0312", "confidence": 0.99, "needs_review": false}
  }
}
```

The example above illustrates the schema only; the `category` and confidence values shown are not guaranteed model output. Your `results.json` should be generated by running the endpoint.
