# ADR-011: Frozen Kubernetes v1.31 Knowledge Snapshot for Corrective RAG

* **Status:** Accepted
* **Date:** 2026-08-23
* **Layer:** Ingestion / Infrastructure / Data

---

## Context

Corrective Retrieval-Augmented Generation (CRAG) evaluates whether retrieved local knowledge base evidence is sufficient to answer a user query. If local evidence is evaluated as inadequate or ambiguous, CRAG dynamically triggers a web search fallback path to retrieve fresh, external evidence.

For this pattern to demonstrate meaningful execution paths:
1. **Local knowledge base must be useful**: It must successfully answer common operational queries (e.g., `kubectl get pods CrashLoopBackOff` troubleshooting) without relying on web search.
2. **Local knowledge base must be deliberately incomplete/stale**: It must fail to answer post-cutoff queries (e.g., version-specific Kubernetes 1.32 features), thereby forcing observable, deterministic fallback to external web search.
3. **Local knowledge base must lack fictional flags**: Queries mentioning fabricated parameters (e.g., `--enable-quantum-scheduler`) must be absent locally and absent on the web, exercising the hallucination checker and refusal path.

Without a versioned, controlled, and reproducible local corpus, CRAG tests would either pass trivially (if live docs contained everything) or break non-deterministically whenever external documentation sites change.

---

## Decision

We freeze a curated **Kubernetes v1.31 Knowledge Base Snapshot** (35 official documentation files) sourced strictly from the canonical upstream repository:
- **Repository**: [kubernetes/website](https://github.com/kubernetes/website)
- **Snapshot Release Tag**: `snapshot-initial-v1.31`
- **Upstream Commit SHA**: `20d164c7a7d092ebc65eed06c855d2ec4f0f0e12`
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)

### Provenance & Version Control Rules
1. **Source Documents Are Truth**: Raw normalized Markdown source files (`data/kb_snapshot/documents/*.md`) and provenance metadata (`manifest.json`, `ATTRIBUTION.md`) are committed directly to Git.
2. **Vector Index Is a Generated Artifact**: Generated Chroma vector store persistent files (`data/chroma/`) are ignored by Git (`.gitignore`) and generated on-demand via `python scripts/build_kb_index.py`.
3. **Offline Snapshot Reproduction**: A dedicated maintenance script (`scripts/fetch_kubernetes_snapshot.py`) reproduces the exact corpus from the immutable GitHub commit SHA and verifies SHA-256 hash integrity. Normal runtime tests remain strictly offline.

---

## Alternatives Considered

### 1. Current Live Kubernetes Documentation
- **Rejected**.
- **Reason**: Live web documentation is constantly updated to reflect current releases (v1.32+). Fetching live docs would eliminate the controlled v1.31 cutoff boundary, breaking the Golden Query 2 staleness test and making tutorial runs non-reproducible.

### 2. Fully Handwritten / Synthetic Documentation
- **Rejected for primary Knowledge Base** (retained only for lightweight unit test fixtures in `tests/fixtures/kb/`).
- **Reason**: Handwritten toy documents lack authentic enterprise document structure, real-world technical depth, and clear license provenance.

### 3. Full Kubernetes Documentation Repository Mirror
- **Rejected**.
- **Reason**: Copying all 1,300+ Markdown files from the upstream website creates excessive local bloat, slows test execution, and fails to model how enterprise teams curate internal operational knowledge bases.

### 4. Curated Frozen v1.31 Subset (Selected)
- **Accepted**.
- **Reason**: Balances authentic enterprise documentation complexity with fast, reproducible local ingestion and an explicit, verifiable version boundary.

---

## Rationale & Key Architectural Insights

### Frozen Source vs. Generated Vector Index
In enterprise AI engineering, vector embeddings and indices are derived artifacts, not source truth. If the embedding model (`ONNX All-MiniLM-L6-v2`), chunk size (500 chars), or vector database (Chroma) is updated, the index is regenerated from the committed source snapshot:

$$\text{Source Documents (Git)} \xrightarrow{\text{Chunker + Embedding Model}} \text{Vector Index (Generated)}$$

### Controlled Staleness Is an Educational Feature
In production systems, stale knowledge represents an operational risk. In this educational architecture, controlled staleness is an intentional design pattern that enables rigorous offline evaluation of CRAG query routing, web fallback mechanisms, and hallucination refusal boundaries.

---

## Production Evolution (Design-Only)

In production enterprise RAG systems, knowledge base freshness is maintained through automated ingestion pipelines rather than static snapshot commits:

- **Source Connectors & CDC**: Automated Change Data Capture (CDC) pipelines monitoring Confluence, Notion, SharePoint, or GitHub repositories.
- **Incremental Indexing**: Computing document delta hashes to add, update, or delete vector chunks without full collection re-indexing.
- **Document Metadata & Versioning**: Tagging chunks with explicit `effective_date`, `doc_version`, and `access_control_group` metadata for filtered retrieval.
- **Freshness SLAs & Approval Workflows**: Automated staging index evaluation prior to production cutover.
