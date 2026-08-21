# Knowledge Base Snapshot

This directory is reserved to house or reference the frozen Kubernetes documentation snapshot used by Use Case 01.

## Rules & Purpose

* **Frozen Corpus:** In future implementation passes, 30–40 official Kubernetes documentation files will be downloaded as a deliberately frozen knowledge snapshot.
* **No Dynamic Refresh:** The local corpus remains unchanged during queries to simulate stale local enterprise documentation.
* **Vector Store Isolation:** Generated Chroma vector stores (`.chroma/` or local DB files) MUST NOT be committed to git.
* **Pass-0 Status:** No documentation snapshot files have been downloaded in Pass-0.
