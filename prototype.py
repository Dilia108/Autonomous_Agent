"""
Minimal Prototype — Vendor Risk Agent
Lab Step 6: Build Minimal Prototype

Two-node LangGraph:
  Node 1: fetch_news  — searches live news about a vendor (Tavily)
  Node 2: classify    — LLM classifies severity and writes evidence

No Flask. No n8n. No scheduling. No RAG.
Run directly:  python prototype.py
"""

import os
import json
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# ── Load API keys from .env ───────────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not OPENAI_API_KEY or not TAVILY_API_KEY:
    raise ValueError("Missing API keys. Copy .env.example to .env and fill in your keys.")

# ── Vendor to test — change this to any supplier name ─────────────────────────
TEST_VENDOR = {
    "name":        "Airbus",          # try any real company name
    "category":    "manufacturing",
    "criticality": "high",
}

# ── State: what gets passed between nodes ─────────────────────────────────────
class AgentState(TypedDict):
    vendor:       dict
    news_results: list
    severity:     str
    evidence:     str
    recommended_action: str

# ── Tools ─────────────────────────────────────────────────────────────────────
llm         = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
search_tool = TavilySearchResults(max_results=3, api_key=TAVILY_API_KEY)

# ── Node 1: fetch_news ────────────────────────────────────────────────────────
def fetch_news(state: AgentState) -> AgentState:
    vendor = state["vendor"]
    query  = f'{vendor["name"]} supply chain risk financial news 2025'

    print(f"\n[Node 1 — fetch_news]")
    print(f"  Searching: {query}")

    results = search_tool.invoke(query)
    state["news_results"] = results if isinstance(results, list) else []

    print(f"  Found {len(state['news_results'])} result(s)")
    for r in state["news_results"]:
        print(f"  · {r.get('url', '')}")

    return state

# ── Node 2: classify ──────────────────────────────────────────────────────────
def classify(state: AgentState) -> AgentState:
    vendor    = state["vendor"]
    news_text = "\n".join(
        r.get("content", r.get("snippet", str(r)))
        for r in state["news_results"]
    )

    print(f"\n[Node 2 — classify]")
    print(f"  Classifying risk for: {vendor['name']}")

    system_prompt = """You are a procurement risk analyst.
Classify vendor risk as LOW, MEDIUM, or HIGH based on recent news.

HIGH   = imminent threat: insolvency, major regulatory action, force majeure, >30% delivery failures.
MEDIUM = elevated concern: leadership instability, labour disputes, single reported delay, financial downgrades.
LOW    = no significant risk signals found.

Respond ONLY with valid JSON — no extra text, no markdown fences:
{
  "severity": "HIGH|MEDIUM|LOW",
  "evidence": "2-3 sentences citing specific news details",
  "recommended_action": "One clear action for the procurement team"
}"""

    user_prompt = f"""Vendor: {vendor['name']}
Category: {vendor['category']}
Criticality: {vendor['criticality']}

Recent news:
{news_text or 'No news results returned.'}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    raw = response.content.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "severity":           "MEDIUM",
            "evidence":           raw[:300],
            "recommended_action": "Manual review required — parsing failed.",
        }

    state["severity"]           = parsed.get("severity", "MEDIUM")
    state["evidence"]           = parsed.get("evidence", "")
    state["recommended_action"] = parsed.get("recommended_action", "")
    return state

# ── Build the 2-node graph ────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("fetch_news", fetch_news)
    g.add_node("classify",   classify)
    g.set_entry_point("fetch_news")
    g.add_edge("fetch_news", "classify")
    g.add_edge("classify",   END)
    return g.compile()

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Vendor Risk Agent — Minimal Prototype")
    print("=" * 55)

    graph = build_graph()

    initial_state: AgentState = {
        "vendor":             TEST_VENDOR,
        "news_results":       [],
        "severity":           "LOW",
        "evidence":           "",
        "recommended_action": "",
    }

    result = graph.invoke(initial_state)

    print("\n" + "=" * 55)
    print("  RESULT")
    print("=" * 55)
    print(f"  Vendor   : {result['vendor']['name']}")
    print(f"  Severity : {result['severity']}")
    print(f"  Evidence : {result['evidence']}")
    print(f"  Action   : {result['recommended_action']}")
    print("=" * 55)

    # ── What to observe ───────────────────────────────────────────────────────
    print("""
What to check after running:
  1. Node 1 printed search URLs  →  Tavily is working
  2. Node 2 produced a severity  →  LLM classification is working
  3. Evidence references a real news detail  →  not hallucinated
  4. Change TEST_VENDOR name and re-run  →  agent generalises

What this prototype does NOT have yet (full agent has these):
  - RAG over internal contracts
  - Conditional routing (alert vs. skip)
  - Flask server for n8n to call
  - Scheduling and deduplication
""")
