# LAB | Autonomous Agent Challenge
## Supplier & Vendor Risk Monitor

---

## 1. Use Case

### Use case description

The Supplier & Vendor Risk Monitor is an autonomous research agent that continuously watches a configured list of vendors, detects risk signals from live news and internal contract documents, classifies severity, and proactively alerts the procurement team — without waiting to be asked.

This project is built on **Option B: Research Assistant**, extended with three capabilities that elevate it to a fully autonomous monitoring agent:

| Layer | Description |
|---|---|
| Base (Option B) | Researches topics across multiple sources, compiles summaries, tracks sources and history |
| Extension 1 — Scheduled monitoring | Runs automatically every 4–6 hours without human initiation, covering the full vendor watchlist |
| Extension 2 — Severity classification & routing | Classifies each research output as LOW / MEDIUM / HIGH and routes only actionable alerts, suppressing noise |
| Extension 3 — RAG-grounded context | Enriches each research cycle with internal vendor contracts and incident history for context-aware assessment |

### Problem statement

Procurement teams manage dozens of suppliers simultaneously but have no systematic way to monitor vendor health in real time. Risk signals — financial distress, news events, delivery failures — only surface after disruption has already occurred, discovered through manual searches, forwarded emails, or supplier self-reporting. By the time a procurement manager acts, the lead time to find an alternative is already compressed.

> **Current gap:** average time-to-awareness of a vendor risk event is 7–14 days.

### Target users

| User | Role | What they need from the agent |
|---|---|---|
| Procurement manager | Primary recipient of HIGH alerts | Enough evidence to make a sourcing decision without further research. Values brevity and a clear recommended action. |
| Supply chain analyst | Manages watchlist and RAG knowledge base | Reviews MEDIUM alerts, decides whether to escalate. Uses the full evidence trail for weekly risk reporting. |
| Finance / risk director | Receives aggregated summaries | Trend data — which vendor categories show elevated risk, which vendors have repeated flags. |

### Current process (how it is done manually today)

1. Analyst manually searches Google News for each vendor name — typically once per week. (~2 hrs/week)
2. Relevant articles are copied into a shared spreadsheet or emailed to the procurement manager with a brief summary note. (~1 hr/week)
3. Procurement manager cross-references contract terms manually — opens PDF, searches by hand — and decides whether to escalate. (~1 hr/week)
4. If escalated, a risk note is written and shared with the finance director, often days after the original signal was found. (~1 hr/event)
5. No tracking or history. Past risk signals are buried in email threads. Pattern detection across vendors is effectively impossible.

**Pain points:** 4–6 hrs/week manual effort · 7–14 day detection lag · no audit trail · no cross-vendor pattern detection.

---

## 2. Technology Stack

### Technology selection framework

| Question | Answer | Technology decision |
|---|---|---|
| Does it need external knowledge? | Yes — internal vendor contracts and SLA terms are not available to the LLM | **RAG** using ChromaDB + OpenAI Embeddings |
| Does it need to interact with external systems? | Yes — fetches live news, delivers Slack alerts | **Tools/integrations**: Tavily Search API, Slack webhook via n8n |
| Does it need multi-step reasoning? | Yes — fetch → retrieve → classify → route is a stateful conditional flow | **LangGraph** for structured workflows |
| Does it need to integrate with business systems? | Yes — scheduling and Slack delivery | **n8n** for orchestration and integrations |
| Does it need to be autonomous? | Yes — runs every 6 hours without human input | **Scheduling + error handling** via n8n |

### Selected technologies

| Technology | Role | Justification |
|---|---|---|
| GPT-4o-mini (OpenAI) | LLM backbone for classification and evidence summarisation | Cost-effective for high-frequency scheduled runs. The task is structured enough that prompt quality matters more than raw model size. |
| ChromaDB | Vector store for RAG | Local, zero-infrastructure setup. Sufficient for up to 20 vendors at MVP scale. Swappable for Pinecone in v2. |
| OpenAI Embeddings | Embedding model for RAG | Consistent with the LLM provider, no additional API key required. |
| LangGraph | Stateful agent reasoning loop | Required for conditional branching (alert vs. skip) and stateful node-to-node context passing. LangChain alone handles linear chains only. |
| LangChain | RAG retrieval chain and tool wiring | Standard retriever interface over ChromaDB. Connects embeddings, vector store, and LLM in a few lines. |
| Tavily Search API | Live news and web signal fetching | Provides sourced, real-time web results without building a custom scraper. Free tier is sufficient for MVP. |
| Flask | Thin HTTP wrapper around the agent | n8n needs a URL to call. Flask adds under 30 lines and keeps the agent core fully decoupled from orchestration. |
| n8n | Scheduling, routing, and Slack delivery | Handles everything that is not AI reasoning: timers, HTTP calls, conditional routing, Slack webhooks — all via no-code nodes. |

### Alternatives considered and trade-offs

| Decision | Alternative considered | Why rejected |
|---|---|---|
| ChromaDB | Pinecone | Requires cloud setup and an additional API key. ChromaDB runs locally — better for MVP speed. |
| LangGraph | Plain LangChain agent | LangChain agents work well for linear flows. This agent has a conditional branch and stateful context passing that LangGraph handles natively. |
| GPT-4o-mini | GPT-4o | GPT-4o is ~10× more expensive per token. The classification task is well-defined with few-shot examples — a smaller model with a strong prompt matches quality at a fraction of the cost. |
| Tavily | Direct web scraping | Custom scrapers require maintenance and bot detection handling. Tavily returns clean, sourced results via API. |
| n8n | Custom Python scheduler (APScheduler) | n8n provides built-in error handling, execution history, and Slack nodes out of the box. Equivalent Python code would require significant additional infrastructure. |

### Architecture overview

```
n8n scheduler (every 6 hrs)
    │
    ▼
POST /run-agent  →  Flask server  →  LangGraph agent
                                          │
                                    ┌─────┴──────┐
                                    ▼            ▼
                              Tavily Search   ChromaDB RAG
                              (live news)     (contracts)
                                    │            │
                                    └─────┬──────┘
                                          ▼
                                  GPT-4o-mini classifies
                                  severity + writes evidence
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                         HIGH / MEDIUM             LOW risk
                         → n8n routes              → logged,
                           to Slack alert            no alert
```

---

## 3. MVP Scope

### Feature brainstorm (all possible features)

- Vendor watchlist management
- News-based signal detection via web search
- Financial data integration (Dun & Bradstreet, Bloomberg)
- RAG over internal vendor contracts
- RAG over incident history documents
- Three-tier severity classification (LOW / MEDIUM / HIGH)
- Custom severity thresholds per industry vertical
- Slack alerts with evidence summary and recommended action
- Email alerts
- Web dashboard with risk timeline
- Deduplication of repeated alerts
- Cross-vendor pattern detection
- ERP / procurement system integration
- Multi-tier supplier mapping (Tier 2, Tier 3)
- Automated mitigation actions (re-sourcing triggers)
- Audit trail and reporting
- Mobile app notifications
- Multi-language support

### Feature categorisation

**Must-have (MVP) — core functionality that solves the main problem:**

- Vendor watchlist of up to 20 named suppliers
- News-based signal detection via Tavily web search
- RAG retrieval over vendor contracts stored in ChromaDB
- Three-tier severity classification: LOW / MEDIUM / HIGH
- Slack alert per MEDIUM or HIGH event including vendor name, severity, evidence, and recommended action
- Scheduled n8n trigger every 4–6 hours
- Deduplication: same vendor and same severity within 24 hours does not re-alert

**Should-have (v2) — important but not critical for first version:**

- Financial API integration (Dun & Bradstreet, Bloomberg)
- Email alerts in addition to Slack
- Audit trail stored in a database
- Cross-vendor pattern detection
- RAG over incident history documents

**Nice-to-have (v3+) — future enhancements:**

- Live ERP / procurement system integration
- Multi-tier supplier mapping (Tier 2 and Tier 3)
- Automated mitigation actions
- Web dashboard with risk timeline
- Multi-language support
- Mobile app notifications

### MVP boundaries

**What is included:**

- `agent.py` — LangGraph reasoning loop (fetch news → retrieve RAG → classify → route)
- `server.py` — Flask REST endpoint (`POST /run-agent`)
- `seed_rag.py` — One-time script to populate ChromaDB with vendor contract text
- `n8n_workflow.json` — Importable workflow for scheduling, routing, and Slack delivery
- `requirements.txt` — All Python dependencies

**What is explicitly excluded:**

- No financial data APIs
- No ERP or CRM integration
- No web UI or dashboard
- No multi-tier supplier coverage
- No automated actions beyond alerting

### Success metrics

| Metric | Target |
|---|---|
| Detection speed | Agent surfaces a verifiable risk event within 6 hours of it appearing in public sources (vs. 7–14 days today) |
| Alert precision | Less than 20% false-positive rate on MEDIUM+ alerts across a 2-week pilot |
| Evidence quality | Every alert cites at least one specific, verifiable source |
| Time saved | Analyst spends less than 30 min/week reviewing output (vs. 4–6 hrs/week today) |
| Action rate | At least 60% of HIGH alerts lead to a documented procurement action within 48 hours |

---

## 4. Risk Assessment

### Technical risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| LLM hallucination in risk classification | Medium | High | Require the LLM to cite a specific news source before raising a HIGH alert. Use few-shot examples in the classification prompt. Add human confirmation for HIGH severity in v2. |
| Alert fatigue from noisy signals | High | High | Implement 24-hour deduplication per vendor per severity tier. Tune classification prompt with real procurement alert examples. Monitor false-positive rate weekly. |
| API rate limits or cost overrun | Medium | Medium | Batch vendor queries per cycle. Cache results for 4 hours. Set monthly spend caps in OpenAI and Tavily dashboards. |
| Integration failure between Flask and n8n | Low | Medium | Add error-handling node in n8n with a dead-letter Slack notification. Keep Flask endpoints stateless and idempotent. |
| Performance degradation on large watchlists | Low | Low | MVP is capped at 20 vendors. For v2 scale, move to async processing with a task queue. |

### Business risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Low user adoption by procurement team | Medium | High | Involve a procurement manager in designing the Slack alert format before launch. Run a 2-week pilot with one team before wider rollout. |
| Scope creep during development | High | Medium | Strictly enforce the MVP feature list. Log all new feature requests to the v2 backlog — do not implement during the MVP sprint. |
| Cost overruns | Low | Medium | Monitor API spend daily during the pilot. Set hard spend limits. Review after week 1. |

### Data risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Stale RAG knowledge base | Medium | Medium | Automate document ingestion via n8n trigger on file upload. Add document timestamp metadata to retrieval results. |
| Poor data quality in vendor contracts | Medium | Medium | Review all documents before ingestion. Chunk at paragraph level to preserve clause context. Test retrieval with 5 sample queries before going live. |
| Privacy and data security | Low | High | Vendor contracts stay in a local ChromaDB instance — no full documents leave the organisation's infrastructure. OpenAI API calls send only news snippets and anonymised contract excerpts. |
| Bias toward English-language news sources | Medium | Low | Noted as a v2 improvement. MVP watchlist is limited to vendors with English-language news coverage. |

---

## 5. Implementation Plan

### Phase 1: Setup and data preparation (Week 1)

**Objective:** Foundation infrastructure and RAG layer working end-to-end.

Tasks:
- Set up Python environment and install all dependencies (`pip install -r requirements.txt`)
- Configure API keys: OpenAI, Tavily
- Collect 3–5 vendor contracts as text or PDF documents
- Run `seed_rag.py` to populate ChromaDB
- Validate RAG retrieval with 5 test queries — confirm relevant contract clauses are returned
- Define vendor watchlist schema (`name`, `category`, `criticality`)

**Milestone:** RAG layer returns accurate context for all vendors in the watchlist.
**Estimated time:** 8–10 hours.

---

### Phase 2: Core agent development (Week 2)

**Objective:** LangGraph agent reasoning loop working standalone, without n8n.

Tasks:
- Build LangGraph graph with four nodes: `fetch_news`, `query_rag`, `classify_severity`, conditional branch to `emit_alert` or `skip_vendor`
- Implement Tavily search tool node
- Write and tune the classification prompt with few-shot examples
- Unit test each node in isolation with mock inputs
- Run end-to-end test with 5 real vendor names and live news search
- Validate output JSON structure matches the expected alert schema

**Milestone:** `python agent.py` produces correct severity classifications and evidence summaries for all test vendors.
**Estimated time:** 10–12 hours.

---

### Phase 3: Integration and testing (Week 3)

**Objective:** Full pipeline connected — agent callable via HTTP, n8n workflow live.

Tasks:
- Build `server.py` Flask wrapper with `POST /run-agent` and `GET /health` endpoints
- Import `n8n_workflow.json` and configure Slack webhook URL
- Test full cycle manually: trigger n8n → HTTP call → agent → Slack alert received
- Implement deduplication logic (timestamp check per vendor per severity)
- Add n8n error-handling branch with dead-letter Slack notification
- Run a single 4-hour live cycle and review all outputs

**Milestone:** Full pipeline runs end-to-end without manual intervention. At least one real alert is delivered to Slack with accurate evidence.
**Estimated time:** 8–10 hours.

---

### Phase 4: Deployment and monitoring (Week 4)

**Objective:** System stable and validated through a 48-hour demo pilot.

Tasks:
- Enable n8n scheduled trigger (every 6 hours)
- Run 48-hour live pilot covering all vendors in the watchlist
- Review every alert manually — log false positives and missed events
- Tune severity thresholds based on observed false-positive rate
- Document agent architecture, prompt versions, and operational runbook
- Record a short walkthrough demo of the running system
- Prepare v2 backlog (financial APIs, ERP integration, audit trail)

**Milestone:** System runs autonomously for 48 hours. False-positive rate is below 20%. Demo walkthrough is recorded.
**Estimated time:** 6–8 hours.

---

### Timeline summary

| Week | Phase | Key milestone | Estimated hours |
|---|---|---|---|
| Week 1 | Setup and data preparation | RAG layer validated | 8–10 hrs |
| Week 2 | Core agent development | Agent runs standalone | 10–12 hrs |
| Week 3 | Integration and testing | Full pipeline live | 8–10 hrs |
| Week 4 | Deployment and monitoring | 48-hr pilot complete | 6–8 hrs |
| **Total** | | | **32–40 hrs** |

### Dependencies

- OpenAI API key with sufficient credits for 4 weeks of scheduled runs
- Tavily API key (free tier sufficient for MVP)
- n8n instance running (local or cloud)
- Slack workspace with incoming webhook configured
- At least 3 real vendor contract documents for RAG seeding

### Resources needed

| Resource | Details |
|---|---|
| Team | 1 developer (solo lab project) |
| LLM API | OpenAI GPT-4o-mini — estimated $2–5 for the full 4-week pilot at 6-hour cycles over 20 vendors |
| Search API | Tavily free tier — 1,000 searches/month, sufficient for MVP |
| Vector DB | ChromaDB local — no cost |
| Orchestration | n8n — free self-hosted or free cloud tier |
| Alerts | Slack free workspace with incoming webhook |

---

## 6. Success Metrics

### Quantitative metrics

| Metric | Dimension | Baseline (today) | Target (MVP) | How measured |
|---|---|---|---|---|
| Time to detect a risk event | Time | 7–14 days | Under 6 hours | Compare alert timestamp to earliest public news timestamp |
| False-positive rate | Quality | N/A | Below 20% | Analyst reviews each MEDIUM+ alert during 2-week pilot |
| Evidence citation rate | Quality | N/A | 100% of alerts cite a verifiable source | Manual review of alert content |
| Analyst monitoring time | Efficiency | 4–6 hrs/week | Under 30 min/week | Self-reported time log during pilot |
| HIGH alert action rate | Impact | N/A | 60% lead to documented action within 48 hrs | Procurement team logs action taken per alert |

### Qualitative indicators

- Procurement manager finds the alert format clear and actionable without needing additional research
- Supply chain analyst trusts the RAG-retrieved contract context and stops cross-checking manually
- At least one real risk event is detected during the 48-hour pilot that would have been missed under the manual process

### Definition of done for MVP

The MVP is considered complete when:

1. The agent runs for 48 hours without manual intervention
2. At least one verifiable MEDIUM or HIGH alert is delivered to Slack with accurate evidence
3. The false-positive rate across the pilot is below 20%
4. The full pipeline (schedule → agent → Slack) can be demonstrated end-to-end in under 5 minutes

---

*Document version: MVP · Aerospace & Defence*
