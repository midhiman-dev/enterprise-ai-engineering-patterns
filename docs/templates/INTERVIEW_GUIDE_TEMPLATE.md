# Interview Guide Template

This document provides a template for use-case interview guides.

> **Evidence Rule:** Claims about repository behavior must be grounded in verified implementation. Production-scale scenarios (such as scaling to 100,000+ documents, millions of chunks, or distributed vector databases) may be discussed as system design reasoning, but must be clearly labeled as unimplemented/unbenchmarked where applicable.

---

## Question Template Structure

When populating questions, use the following structure:

### [Question Title / Topic]

#### Short Interview Answer
A concise, direct answer (30–60 seconds) suitable for an initial interview response.

#### Deeper Explanation
Technical deep dive detailing underlying concepts, mechanisms, and trade-offs.

#### Repository Evidence
What does the actual implementation demonstrate? Direct references to repository source files, layer boundaries, or test suites.

#### Production Evolution
How would the architecture evolve beyond tutorial scale (e.g., scaling from 40 docs to 100,000+ docs, millions of chunks, distributed vector DBs, embedding migration, sharding)?

#### Failure Modes / Trade-offs
What can go wrong, edge cases, cost implications, or performance bottlenecks.

#### Metrics / Evaluation
Empirical benchmark data, trace evidence, or test logs from the repository (where applicable).

#### Evidence Status
`Implemented` | `Tested` | `Measured` | `Design-only`

#### Likely Follow-up Questions
Questions interviewers are likely to ask next based on this response.

---

## Level 1 — Fundamentals

*Concept and implementation questions covering core workflow mechanics, state management, and Clean Architecture boundaries.*

## Level 2 — Failure and Debugging Scenarios

*Real-world failure modes, including weak retrieval, stale evidence, chunking issues, hallucination detection, grader false positives/negatives, and provider errors.*

## Level 3 — Production and Scale

*System design considerations for scaling retrieval, managing multi-tenant latency, hybrid search, caching, re-ranking, document freshness, and cost control.*

## Level 4 — Architecture Judgment

*High-level trade-off evaluation: when NOT to use RAG, SQL vs vector search, agents vs deterministic pipelines, fine-tuning vs retrieval, and CRAG complexity budgets.*
