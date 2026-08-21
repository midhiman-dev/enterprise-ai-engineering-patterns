# Architecture Overview — Use Case 01: Corrective RAG

> **Current Status:** Scaffolding established. Detailed architectural diagrams and component breakdowns will be added as layers are implemented.

## System Architecture

```text
┌──────────────────────────────────────────────────────────┐
│ API Layer (FastAPI)                                      │
│ Endpoints, DTO Schemas, Streaming SSE                    │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Application Layer                                        │
│ LangGraph Workflow Orchestration                         │
│ Node handlers, Graph State, Conditional Edge Routing      │
└──────────────┬─────────────────────────────┬─────────────┘
               │                             │
               │ invokes ports               │ records traces
               ▼                             ▼
┌──────────────────────────────┐ ┌──────────────────────────┐
│ Domain Layer (Pure Python)   │ │ Decision Trace Repository│
│ Entities & Port Interfaces   │ │ (Domain Port)            │
└──────────────▲───────────────┘ └─────────────▲────────────┘
               │                               │
               │ implements ports              │ implements port
┌──────────────┴───────────────────────────────┴────────────┐
│ Infrastructure Layer                                     │
│ Chroma Retr., OpenAI Gen., Tavily Search, SQLite Persistence│
└──────────────────────────────────────────────────────────┘
```

## Architectural Principles

1. **Pure Domain Core:** Domain contains zero dependencies on external frameworks, databases, or AI vendor SDKs.
2. **LangGraph Visibility:** LangGraph orchestration is explicitly placed in the Application layer, making graph state, nodes, edges, routing, and retries clearly visible to learners.
3. **Provider Isolation:** External LLMs, vector stores, and web search engines implement abstract Domain ports. Replacing a vendor (e.g., swapping OpenAI for Ollama, or Chroma for Qdrant) requires zero changes to the Domain or Application layers.
