```markdown
# Enterprise AI Engineering Patterns

Production-ready blueprints and design patterns for building scalable, reliable, and auditable GenAI applications using Clean Architecture (Ports & Adapters).

Most AI tutorials stop at monolithic Python scripts, fragile Jupyter notebooks, or tightly coupled LangChain wrappers. This repository bridges the gap between toy prototypes and enterprise-grade software engineering — demonstrating how to isolate domain logic from LLM vendors, build resilient agentic loops, enforce safety guardrails, and run systematic evaluations.

## Architectural Principles

Every pattern in this repository strictly adheres to inward-facing dependency rules:

```
UI (React/Next.js) ──► API (FastAPI) ──► Application (Orchestrators/Graphs) ──► Domain (Pure Python)
                                                  │                               ▲
                                                  └──► Infrastructure (Adapters) ─┘
```

- **Domain Layer (Pure Python)**: Entities, value objects, and abstract Ports (`typing.Protocol`). Zero third-party LLM or database imports.
- **Application Layer**: Use cases and orchestration logic (e.g., LangGraph state machines) relying solely on domain ports.
- **Infrastructure Layer**: Concrete adapters implementing domain ports (OpenAI, Anthropic, ChromaDB, Tavily, NeMo Guardrails).
- **Composition Root**: Explicit dependency injection at runtime — hot-swap providers without touching business logic.
- **Full Auditability**: Every decision, routing step, and grading score is captured via a structured `DecisionTrace`.

## Pattern Catalog

| Pattern                              | Focus Area                                              | Key Technologies                          | Status    |
|--------------------------------------|---------------------------------------------------------|-------------------------------------------|-----------|
| 01. Corrective RAG (CRAG)            | Self-correcting retrieval, query rewriting, hallucination grading | LangGraph, ChromaDB, Tavily, FastAPI, React | Active    |
| 02. Multi-Agent Systems              | Supervisor patterns, task planning, human-in-the-loop   | LangGraph, AutoGen, Redis                 | Upcoming  |
| 03. Model Context Protocol (MCP)     | Standardized agent-to-tool & data context interfaces    | MCP SDK, FastMCP, PostgreSQL              | Upcoming  |
| 04. Responsible AI & Guardrails      | PII redaction, prompt injection defense, policy moderation | NeMo Guardrails, Llama Guard, Presidio  | Upcoming  |
| 05. GenAI Evaluation & Observability | RAG Triad, LLM-as-a-Judge, latency/token tracing        | DeepEval, Ragas, OpenTelemetry            | Upcoming  |

## Featured Blueprint: Corrective RAG (CRAG)

The first pattern implements a **Cloud & Kubernetes Troubleshooting Assistant** designed to solve the real-world operational problem of stale internal documentation.

### Core Routing Paths

```
                        ┌──────────────────┐
                        │   User Query     │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Retrieve Context │
                        └────────┬─────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Grade Document Match  │
                     └───────┬───────┬───────┘
            Relevant         │       │    Irrelevant / Stale
         ┌───────────────────┘       └───────────────────┐
         ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐
│  Generate Answer │                           │  Rewrite Query   │
└────────┬─────────┘                           └────────┬─────────┘
         │                                               │
         ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐
│  Hallucination   │◄──────────────────────────│   Web Search     │
│      Check       │                           │     (Tavily)     │
└────────┬─────────┘                           └──────────────────┘
         │
    Passed Grader ──► Final Answer + Audit Trace
```

- **Happy Path**: Common K8s issue → local retrieval passes relevance → direct generation.
- **Stale/Correction Path**: Query post-dates the static snapshot → relevance check fails → query rewrite → live Tavily web search fallback → generation.
- **Hallucination Guardrail Path**: Fabricated flags/commands → hallucination grader catches unsupported generation → loop to reject or regenerate.

## Quick Start

### 1. Clone & Set Up Workspace

```bash
git clone https://github.com/midhiman-dev/enterprise-ai-engineering-patterns.git
cd enterprise-ai-engineering-patterns
```

### 2. Configure Environment

```bash
cp .env.example .env
# Add your OPENAI_API_KEY and TAVILY_API_KEY in .env
```

### 3. Run Use Case 1 (Corrective RAG)

```bash
cd patterns/01_corrective_rag
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start API
uvicorn src.api.main:app --reload --port 8000
```

## Contributing

Contributions are welcome! Please ensure that any new pattern follows the strict **Domain → Application → Infrastructure** folder separation and includes corresponding unit and integration tests.

## License

This project is licensed under the MIT License.
```
