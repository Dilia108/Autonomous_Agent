# Autonomous Agent Challenge

Supplier and Vendor Risk Monitor for the Aerospace industry.

This repository contains a minimal LangGraph prototype for an autonomous vendor-risk research agent. The goal is to monitor suppliers with live web search, classify risk severity, and support procurement decisions with concise evidence.

## Project Summary

The full challenge concept is described in [Autonomous Agent Challenge.md](Autonomous%20Agent%20Challenge.md). In short, the target system:

- Watches a list of vendors continuously
- Searches live news for risk signals
- Uses RAG over internal contract documents in the full version
- Classifies severity as `LOW`, `MEDIUM`, or `HIGH`
- Routes actionable alerts to the procurement team
- Runs on a schedule without human initiation

## Prototype

The current code in [`prototype.py`](prototype.py) is a minimal proof of concept with two LangGraph nodes:

1. `fetch_news` searches live news with Tavily
2. `classify` uses `gpt-4o-mini` to assign severity and write evidence

This prototype is intentionally smaller than the full autonomous agent. It does **not** yet include:

- RAG over internal contracts
- Conditional routing for alert vs. skip
- Flask server for n8n
- Scheduling
- Deduplication

## Evidence

See [Prototype_evidence.md](Prototype_evidence.md) for the run notes and output examples.

Screenshots used as testing evidence:

- [Boeing test](screenshots/image.png)
- [Airbus test](screenshots/image-1.png)

## Tech Stack

- LangGraph
- LangChain
- OpenAI `gpt-4o-mini`
- Tavily Search API
- `python-dotenv`
- ChromaDB for the full RAG version
- Flask and n8n for the full autonomous workflow

## Repository Files

- `prototype.py` - runnable minimal prototype
- `Autonomous Agent Challenge.md` - project brief and architecture
- `Prototype_evidence.md` - prototype results and screenshots
- `requirements.txt` - Python dependencies

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with:

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
```

## Run the Prototype

```bash
python prototype.py
```

By default, the script tests the vendor `Airbus`. You can change the `TEST_VENDOR` dictionary in [`prototype.py`](prototype.py) to try a different supplier.

## Expected Output

When the script runs successfully, it should:

- Print the Tavily search query and returned URLs
- Print a severity classification
- Produce an evidence summary grounded in the fetched news
- Produce one recommended procurement action

## Notes

- `prototype.py` is a demonstration script, not the final production workflow.
- The full challenge description includes a more autonomous design with n8n scheduling, alert routing, and RAG-backed context.
- Vendor risk monitoring is only as good as the news and documents it can access, so the evidence trail matters as much as the severity label.

