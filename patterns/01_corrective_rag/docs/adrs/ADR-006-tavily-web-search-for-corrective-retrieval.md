# ADR-006: Tavily Web Search for Corrective Retrieval

## Status

Accepted

## Context

In a Corrective RAG (CRAG) architecture, local vector retrieval can fail to provide relevant evidence when:
* **Knowledge Base Incompleteness**: The local vector database is intentionally frozen or contains a partial snapshot of documentation.
* **Freshness Gap**: The user asks about recent software updates, release notes, or version-specific troubleshooting policies not indexed locally.
* **Domain Misalignment**: The internal corpus lacks coverage for the specific error code or deployment scenario.

When the `RelevanceGrader` evaluates all retrieved local chunks as irrelevant, the graph branches to corrective retrieval:
```text
Local KB Retrieval
       ↓
Relevance Grading  ──(No Relevant Candidates)──>  Query Rewriter
                                                       ↓
                                                Web Search Provider (Tavily)
                                                       ↓
                                                Domain Documents
                                                       ↓
                                                Generator
```

To execute external retrieval, the infrastructure layer requires a concrete implementation of the `WebSearchProvider` Domain port.

## Decision

We select **Tavily Search API** (`TavilyWebSearchProvider`) as the primary infrastructure web search adapter for Corrective RAG.

### Core Architectural Principles

1. **Strict Domain Port Isolation**:
   `TavilyWebSearchProvider` structurally implements `WebSearchProvider` (`search(question: Question) -> Sequence[Document]`). Neither the Domain entities nor the LangGraph Application nodes import Tavily SDK objects, response dictionaries, or vendor-specific exceptions.
2. **Provider Ranking Score != Answer Relevance**:
   Tavily may return a provider-defined score with search results. The application does not assume that this score is calibrated semantic relevance for the user's question. It **MUST NOT** be treated as equivalent to a downstream semantic `RelevanceGrader` decision or hallucination metric. It is preserved strictly as provider metadata (`Document.metadata["tavily_score"]`).
3. **Operational Failure vs. Empty Search Distinction**:
   - **Tavily returns zero results (`{"results": []}`)**: Valid retrieval outcome. Returns `[]` cleanly. The graph proceeds with available state.
   - **Tavily API unavailable / rate limited / unauthorized**: Operational failure. Raises a generic `RuntimeError("Tavily search request failed.")` chained with `from exc` to preserve observability.

## Alternatives Considered

### 1. Tavily Search API (Selected)
* **Pros**: Built specifically for LLM and RAG workflows; returns pre-parsed content snippets and canonical URLs; free tier for educational environments; fast JSON API integration.
* **Trade-offs**: External third-party API dependency; search quality and ranking controlled by vendor; rate/credit limits on free tiers.

### 2. Bing Web Search / Azure AI Search Web Retrieval
* **Pros**: Enterprise compliance capabilities and broad index coverage.
* **Trade-offs**: Complex setup, enterprise subscription requirements, and heavy configuration footprint unsuitable for lightweight learner onboarding.

### 3. SerpAPI / Commercial Search Engine Wrappers
* **Pros**: Wraps mainstream search engine result pages (Google, Bing).
* **Trade-offs**: Pay-per-query cost structure; potential terms-of-service fragility; requires HTML parsing wrappers for snippet extraction.

### 4. Direct Custom Web Scraping
* **Pros**: Maximum control over scraping and parsing logic.
* **Trade-offs**: Fragile HTML parsing; anti-bot blocking; legal/robots.txt compliance issues; high engineering maintenance burden.

## Critical Enterprise Risk: External Web Evidence

Integrating external web search into enterprise RAG systems introduces risks not present in controlled internal vector stores:

1. **Untrusted Content & Untrusted Sources**: Web search returns external pages whose accuracy, security posture, and authority cannot be guaranteed.
2. **Prompt Injection & Retrieval Poisoning**: Malicious web pages may embed indirect prompt injections designed to hijack downstream LLM generation.
3. **Data Leakage & Privacy Risks**: Sending user questions to external web search APIs may expose sensitive internal system names, IP addresses, proprietary error logs, or PII.

### Production Mitigations (Design-Only — Not Implemented in Pass-10)

In enterprise production deployments, external web retrieval requires additional security controls:
* **Pre-Search Policy Checks**: Redacting PII, credentials, and internal hostnames from queries before external API dispatch.
* **Allowlist / Denylist Filtering**: Restricting external search queries to trusted domain boundaries (e.g. `include_domains=["kubernetes.io", "github.com"]`).
* **Evidence Sanitization & Isolation**: Treating web evidence as untrusted data strings within strict LLM system prompt boundaries.

## Senior Interview Lessons & Takeaways

### Q1: "Why use web search only after local retrieval fails?"
> **Answer**: Local retrieval is faster, cheaper, private, and operates over curated, trusted enterprise data. External web search introduces network latency, API costs, external data leakage risks, and untrusted content. A Corrective RAG graph uses web search as a fallback strategy only when internal evidence is insufficient.

### Q2: "How should a system handle an empty search result from Tavily?"
> **Answer**: An empty result set is a valid search outcome, not an infrastructure exception. The search adapter returns an empty sequence `[]`. The graph proceeds down the fallback or safe-refusal path based on available evidence rather than throwing operational errors.

### Q3: "Does a high search engine score guarantee the retrieved document is relevant?"
> **Answer**: No. A Tavily result score is provider-defined retrieval metadata. I would not treat it as equivalent to my application's relevance grade or grounding decision. Those are separate stages with different semantics.
