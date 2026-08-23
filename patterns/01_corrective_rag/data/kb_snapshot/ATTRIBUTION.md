# Corpus Attribution and Licensing Notice

This directory (`data/kb_snapshot/`) contains documentation source files derived from the official **Kubernetes Documentation** repository.

## Upstream Provenance

- **Source**: Kubernetes Documentation
- **Upstream Repository**: [kubernetes/website](https://github.com/kubernetes/website)
- **Snapshot Release Tag**: `snapshot-initial-v1.31`
- **Upstream Commit SHA**: `20d164c7a7d092ebc65eed06c855d2ec4f0f0e12`
- **Kubernetes Version**: 1.31
- **License**: Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))
- **Upstream License File**: [LICENSE](https://github.com/kubernetes/website/blob/main/LICENSE)

## Local Transformation & Normalization

The source files included in `data/kb_snapshot/documents/` represent a curated subset (35 documents) selected specifically for educational testing of Corrective Retrieval-Augmented Generation (CRAG).

The following deterministic transformations were applied during ingestion:
1. **Front Matter Stripping**: Hugo YAML front matter (`--- ... ---`) was parsed to extract original document titles and then stripped to simplify text chunking.
2. **Shortcode Normalization**: Hugo-specific shortcodes (e.g. `{{< note >}}`, `{{< warning >}}`) were stripped to plain text.
3. **Heading Alignment**: Standard Markdown `# Title` top-level headers were ensured at the beginning of each file.
4. **Technical Content**: 100% of the underlying technical content, commands, and code blocks from the v1.31 documentation were preserved without modification, summarizing, or rephrasing.

## Disclaimer

This repository (`enterprise-ai-engineering-patterns`) is an independent educational repository. It is **not** affiliated with, endorsed by, or sponsored by Kubernetes, the Cloud Native Computing Foundation (CNCF), or The Linux Foundation.
