# Frozen Kubernetes v1.31 Knowledge Base Snapshot

This directory contains the frozen, version-controlled Kubernetes v1.31 local Knowledge Base snapshot used for testing Corrective Retrieval-Augmented Generation (CRAG).

## Overview & Staleness Rationale

The CRAG pattern relies on a local knowledge base that is **useful but deliberately incomplete/stale**.

- **Version Cutoff:** Frozen at **Kubernetes v1.31** (upstream tag `snapshot-initial-v1.31`, commit `20d164c7a7d092ebc65eed06c855d2ec4f0f0e12`).
- **Intentional Gap:** Post-v1.31 behavior (e.g. Kubernetes 1.32 feature queries) is **absent** from this corpus, forcing the CRAG application to trigger corrective web search fallback.
- **Absence Property:** Fictional flags (e.g. `--enable-quantum-scheduler`) have **zero** occurrences in this corpus, exercising the grounding and refusal safety path.

## Directory Layout

```
data/kb_snapshot/
├── README.md           # Corpus description & maintenance documentation
├── ATTRIBUTION.md      # CC BY 4.0 license & upstream provenance details
├── manifest.json       # Versioned document manifest with SHA-256 hashes
└── documents/          # 35 normalized Markdown content files
```

## Reproduction & Verification Commands

To verify snapshot integrity against `manifest.json`:
```bash
python scripts/fetch_kubernetes_snapshot.py --verify-only
```

To re-fetch the snapshot from upstream GitHub:
```bash
python scripts/fetch_kubernetes_snapshot.py
```

To index the snapshot into Chroma vector store:
```bash
python scripts/build_kb_index.py
```
