# Interview Guide Template

This document provides a template for use-case interview guides. Interview questions and answers are written only after code implementation provides verified empirical evidence.

---

## Question Template Structure

When populating questions, use the following structure:

### [Question Title / Topic]

#### Short Interview Answer
A concise, direct answer (30–60 seconds) suitable for an initial interview response.

#### Deeper Explanation
Technical deep dive detailing underlying concepts, mechanisms, and trade-offs.

#### How the Repository Implements or Demonstrates This
Direct references to repository source files, layer boundaries, or tests that prove this pattern.

#### Failure Modes / Trade-offs
What can go wrong, edge cases, cost implications, or performance bottlenecks.

#### Metrics or Evidence
Empirical benchmark data, trace evidence, or test logs from the repository.

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
