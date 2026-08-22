# ADR-005: LLM Query Rewriting for Corrective Retrieval

## Status

Accepted

## Context

In a Corrective RAG (CRAG) system, local vector retrieval can fail to return sufficient evidence for several reasons:
* **Stale Knowledge Base**: The internal vector store contains a snapshot of documentation that omits newer software features or version-specific policies (e.g. Kubernetes 1.32 node-pressure eviction policy).
* **Conversational Wording**: Users ask questions with conversational filler, meta-language, or indirect phrasing (e.g., *"Can someone please explain to me how I should handle pod eviction when..."*).
* **Vocabulary Mismatch**: The terminology used in the user's prompt differs from vendor documentation keywords or search engine index terms.

When relevance evaluation grades local candidates as insufficient or irrelevant, the CRAG workflow routes to external web search. However, passing the user's raw conversational question directly to external search engines can yield poor retrieval precision and recall.

A dedicated **Query Rewriter** reformulates the user question into a concise, technical search query optimized for external search engines and vendor documentation sites.

## Decision

We implement **`GroqQueryRewriter`** as a concrete Infrastructure adapter for the Domain `QueryRewriter` port using Groq hosted LLMs.

### Core Architectural Rule: Original Question vs. Rewritten Search Query

```text
Original User Question  --->  User Intent (Preserved Immutable) ---> Generator Prompt
                                                                           ▲
                                                                           │ Grounded
Rewritten Query         --->  Search Strategy Only              ---> Web Search evidence
```

The system strictly distinguishes between user intent and search strategy:
* **`question` (Original User Question)**: Immutable representation of user intent. It remains authoritative throughout the workflow state (`GraphState["question"]`) and is supplied to the final `Generator` to ensure the model answers what the user actually asked.
* **`rewritten_question` (Rewritten Search Query)**: A retrieval-optimization artifact stored separately in workflow state (`GraphState["rewritten_question"]`). It is consumed solely by the search provider (`WebSearchProvider`) to retrieve relevant evidence documents.

**The rewritten query MUST NOT replace or overwrite the original question in application state.**

### Key Implementation Principles

1. **Clean Domain Boundary**: `GroqQueryRewriter` structurally satisfies the `QueryRewriter` port (`rewrite(question: Question) -> Question`) without inheriting from vendor classes or exposing Groq SDK details to Application or Domain layers.
2. **Defensive Search Prompting**: The model is instructed to:
   - Strip conversational filler and meta-language.
   - Preserve technical intent, core concepts, and explicit version identifiers (e.g. `Kubernetes 1.32`).
   - Refrain from answering the question or establishing whether user premises (e.g. fictitious flags like `--enable-quantum-scheduler`) actually exist.
   - Treat user text strictly as input data to reformulate, preventing prompt-injection overrides.
3. **Provider Failure Isolation**: Blank outputs or API failures raise operational `RuntimeError` exceptions. Infrastructure failures are never silently swallowed or converted into fake search queries.

## Alternatives Considered

### 1. Use Original Query Directly
* **Pros**: Zero additional LLM latency, zero API cost, zero risk of query drift or intent distortion.
* **Trade-offs**: Conversational filler and meta-language reduce search engine precision and recall for technical vendor documentation.

### 2. Deterministic Rule-Based Rewrite (Heuristics / Regex)
* **Pros**: Ultra-fast, zero cost, 100% deterministic and auditable (e.g. strip "How do I", append "Kubernetes documentation").
* **Trade-offs**: Brittle across diverse user phrasing and fails to handle complex semantic reformulations.

### 3. LLM Query Rewrite (Selected)
* **Pros**: High semantic flexibility; removes conversational fluff while preserving technical keywords and version numbers across arbitrary user phrasings.
* **Trade-offs**: Introduces LLM API latency and cost per fallback execution; introduces probabilistic behavior and potential query drift.

### 4. Multi-Query Expansion (Design-Only — Not Implemented in Pass-9)
* **Pros**: Generates multiple search query variants to maximize recall across diverse document collections.
* **Trade-offs**: Increases downstream search API costs, requires deduplication, and demands candidate reranking.

## Critical Architectural Risk: Query Drift

Query rewriting is an **optimization**, not a guaranteed improvement. An LLM query rewriter can exhibit **query drift**:
* Removing a critical version number (e.g. dropping `1.32` from `Kubernetes 1.32`).
* Over-specifying or introducing inaccurate technical terms.
* Distorting the user's underlying technical topic.

Because rewriting is probabilistic, a rewritten query can sometimes yield *worse* retrieval results than the original question. Keeping the original question immutable for final answer generation mitigates the risk of producing an answer to the wrong question.

## Production Evolution (Design-Only — Not Implemented in Pass-9)

In enterprise production deployments, query rewriting evolves into a comprehensive retrieval optimization pipeline:

```text
Original Question + Rewritten Query
                 ↓
      Multi-Query Parallel Search
                 ↓
    Document Result Merging & Deduplication
                 ↓
         Cross-Encoder Reranking
                 ↓
   Top-K Evidence for Generator
```

* **Multi-Query Fusion**: Executing search against both the original question and 2–3 rewritten variants, then merging and deduplicating results via Reciprocal Rank Fusion (RRF).
* **Reranking**: Passing retrieved search candidates through a cross-encoder reranker (e.g., Cohere or BGE-Reranker) before feeding evidence to the generator.
* **Retrieval Metric Evaluation**: Evaluating query rewriter performance on golden datasets using empirical retrieval metrics:
  - **Hit@K**: Does the retrieved top-K set contain at least one gold evidence chunk?
  - **Recall@K**: What proportion of gold evidence chunks are retrieved?
  - **MRR (Mean Reciprocal Rank)**: At what rank position does the first relevant evidence document appear?

## Senior Interview Lessons & Takeaways

### Q1: "Should you always rewrite the user's query before RAG retrieval?"
> **Answer**: No. Query rewriting introduces an extra LLM call, latency, cost, and the risk of query drift. For clear, keyword-dense technical queries, the original user query is often already optimal. In production, query rewriting should be selectively enabled based on offline retrieval benchmarks (Hit@K, MRR) comparing original vs. rewritten query performance.

### Q2: "What if query rewriting changes the user's intent?"
> **Answer**: We preserve the user's original question as immutable domain state (`state["question"]`) and use the rewritten query strictly for search retrieval (`state["rewritten_question"]`). The final generator always answers the original user question grounded in retrieved evidence.

### Q3: "What is the ultimate success criterion for a Query Rewriter?"
> **Answer**: The success criterion for a Query Rewriter is **NOT** that its output sounds more polished or professional. The sole metric of success is whether the rewritten query causes downstream retrieval to find higher-quality evidence documents.
