# Use Case 01 — Interview Guide

> **Current Status:** Placeholder. Questions and answers will be populated as implementation proceeds. Claims about repository behavior will be grounded in verified implementation, while production-scale scenarios will be clearly labeled as system design reasoning.

## Overview

This guide will prepare AI engineers and system designers to discuss Corrective RAG (CRAG) architecture, trade-offs, failure modes, and production scaling in technical interviews.

## Planned Topics

* **Level 1 — Fundamentals:** CRAG workflow mechanics, LangGraph state management, and Clean Architecture layer isolation.
* **Level 2 — Failure & Debugging:** Handling weak local retrieval, query re-writing strategies, hallucination grading false positives/negatives, and bounded retries.
* **Level 3 — Production & Scale:** Vector store scale, hybrid search, caching, multi-tenant security, and embedding migration.
* **Level 4 — Architecture Judgment:** Determining when CRAG is overengineering, comparing deterministic pipelines vs. agentic workflows, and fine-tuning vs. RAG.
