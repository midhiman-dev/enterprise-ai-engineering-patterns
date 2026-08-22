# Pattern 01 Assignment — Corrective RAG

## Problem Statement

Design and build a **Corrective RAG system** for an enterprise technical support scenario.

A software company maintains an internal troubleshooting knowledge base for one of its enterprise products. The knowledge base contains product manuals, configuration guides, known-error documentation, troubleshooting notes, and operational guidance.

The challenge is that the internal knowledge base is **not always complete or current**.

New versions of the product are released regularly, and some fixes, features, configuration changes, or operational guidance may only exist in newer documentation or external sources.

The support assistant must therefore be able to work with an imperfect local knowledge base without blindly trusting whatever retrieval returns.

## Your Task

Choose a realistic enterprise software product or technical platform and build a solution that applies the **Corrective RAG pattern**.

Do not use Kubernetes, since Kubernetes troubleshooting is the reference implementation for this pattern.

Your system should help a support engineer answer technical questions using local enterprise knowledge while being able to recognize when that knowledge is inadequate.

## Constraints

- The local knowledge base must be intentionally incomplete, stale, or both.
- Some questions must be answerable using only local knowledge.
- Some questions must require information that is not available in the local knowledge base.
- The system must handle unsupported or fabricated technical assumptions safely.
- The solution must follow **Clean Architecture / Ports and Adapters** principles.
- Core business/application logic must remain independent of specific LLM, vector database, and search-provider SDKs.
- The system should be testable without requiring every external provider to be live.
- The solution should use realistic technical documentation rather than toy text examples.
- The implementation should clearly distinguish what has been implemented and tested from what is only proposed for production-scale evolution.

## Expected Learning Outcome

By completing the assignment, you should be able to explain:

- why standard RAG can fail when enterprise knowledge becomes stale or incomplete
- how Corrective RAG changes the behavior of the system
- how you designed the system to react when retrieved knowledge is insufficient
- how your architecture avoids coupling the application to specific AI providers
- what trade-offs you made around retrieval, external knowledge, grounding, reliability, cost, and latency
- how the solution would evolve for a much larger enterprise knowledge base

The goal is not to reproduce the reference implementation.

The goal is to apply the **Corrective RAG pattern** independently to a different enterprise problem and justify your architectural decisions.
