#!/usr/bin/env python3
"""Maintenance script to fetch and reproduce the frozen Kubernetes v1.31 KB snapshot.

Fetches 35 curated documentation files from the canonical upstream repository:
https://github.com/kubernetes/website at tag snapshot-initial-v1.31 (commit 20d164c7a7d092ebc65eed06c855d2ec4f0f0e12).

Normalizes Hugo front matter cleanly while preserving 100% technical content,
writes to data/kb_snapshot/documents/, and generates data/kb_snapshot/manifest.json.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from typing import Any, Dict, List, Tuple
import urllib.request

SOURCE_REPOSITORY = "https://github.com/kubernetes/website"
SOURCE_TAG = "snapshot-initial-v1.31"
SOURCE_COMMIT = "20d164c7a7d092ebc65eed06c855d2ec4f0f0e12"
KUBERNETES_VERSION = "1.31"
LICENSE = "CC-BY-4.0"

# Curated allowlist of 35 production troubleshooting documents from upstream website tree
DOCUMENT_ALLOWLIST: List[Dict[str, str]] = [
    {
        "upstream_path": "content/en/docs/concepts/workloads/pods/pod-lifecycle.md",
        "local_filename": "pod-lifecycle.md",
        "category": "Workloads & Pods",
    },
    {
        "upstream_path": "content/en/docs/concepts/workloads/pods/init-containers.md",
        "local_filename": "init-containers.md",
        "category": "Workloads & Pods",
    },
    {
        "upstream_path": "content/en/docs/concepts/workloads/controllers/deployment.md",
        "local_filename": "deployment.md",
        "category": "Workloads & Controllers",
    },
    {
        "upstream_path": "content/en/docs/concepts/workloads/controllers/replicaset.md",
        "local_filename": "replicaset.md",
        "category": "Workloads & Controllers",
    },
    {
        "upstream_path": "content/en/docs/concepts/workloads/controllers/job.md",
        "local_filename": "job.md",
        "category": "Workloads & Controllers",
    },
    {
        "upstream_path": "content/en/docs/concepts/workloads/controllers/cron-jobs.md",
        "local_filename": "cron-jobs.md",
        "category": "Workloads & Controllers",
    },
    {
        "upstream_path": "content/en/docs/concepts/scheduling-eviction/node-pressure-eviction.md",
        "local_filename": "node-pressure-eviction.md",
        "category": "Scheduling & Eviction",
    },
    {
        "upstream_path": "content/en/docs/concepts/scheduling-eviction/pod-priority-preemption.md",
        "local_filename": "pod-priority-preemption.md",
        "category": "Scheduling & Eviction",
    },
    {
        "upstream_path": "content/en/docs/concepts/scheduling-eviction/taint-and-toleration.md",
        "local_filename": "taint-and-toleration.md",
        "category": "Scheduling & Eviction",
    },
    {
        "upstream_path": "content/en/docs/concepts/scheduling-eviction/pod-overhead.md",
        "local_filename": "pod-overhead.md",
        "category": "Scheduling & Eviction",
    },
    {
        "upstream_path": "content/en/docs/concepts/services-networking/dns-pod-service.md",
        "local_filename": "dns-pod-service.md",
        "category": "Services & Networking",
    },
    {
        "upstream_path": "content/en/docs/concepts/services-networking/service.md",
        "local_filename": "service.md",
        "category": "Services & Networking",
    },
    {
        "upstream_path": "content/en/docs/concepts/services-networking/cluster-ip-allocation.md",
        "local_filename": "cluster-ip-allocation.md",
        "category": "Services & Networking",
    },
    {
        "upstream_path": "content/en/docs/concepts/storage/persistent-volumes.md",
        "local_filename": "persistent-volumes.md",
        "category": "Storage",
    },
    {
        "upstream_path": "content/en/docs/concepts/configuration/configmap.md",
        "local_filename": "configmap.md",
        "category": "Configuration & Secrets",
    },
    {
        "upstream_path": "content/en/docs/concepts/configuration/secret.md",
        "local_filename": "secret.md",
        "category": "Configuration & Secrets",
    },
    {
        "upstream_path": "content/en/docs/concepts/cluster-administration/logging.md",
        "local_filename": "logging.md",
        "category": "Cluster Administration & Diagnostics",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-application/debug-pods.md",
        "local_filename": "debug-pods.md",
        "category": "Application Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-application/debug-running-pod.md",
        "local_filename": "debug-running-pod.md",
        "category": "Application Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-application/debug-init-containers.md",
        "local_filename": "debug-init-containers.md",
        "category": "Application Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-application/debug-service.md",
        "local_filename": "debug-service.md",
        "category": "Application Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-application/determine-reason-pod-failure.md",
        "local_filename": "determine-reason-pod-failure.md",
        "category": "Application Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-application/get-shell-running-container.md",
        "local_filename": "get-shell-running-container.md",
        "category": "Application Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-cluster/monitor-node-health.md",
        "local_filename": "monitor-node-health.md",
        "category": "Cluster & Node Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-cluster/troubleshoot-kubectl.md",
        "local_filename": "troubleshoot-kubectl.md",
        "category": "Cluster & Node Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/debug/debug-cluster/kubectl-node-debug.md",
        "local_filename": "kubectl-node-debug.md",
        "category": "Cluster & Node Debugging",
    },
    {
        "upstream_path": "content/en/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes.md",
        "local_filename": "configure-liveness-readiness-startup-probes.md",
        "category": "Pod & Container Configuration",
    },
    {
        "upstream_path": "content/en/docs/tasks/configure-pod-container/assign-cpu-resource.md",
        "local_filename": "assign-cpu-resource.md",
        "category": "Pod & Container Configuration",
    },
    {
        "upstream_path": "content/en/docs/tasks/configure-pod-container/assign-memory-resource.md",
        "local_filename": "assign-memory-resource.md",
        "category": "Pod & Container Configuration",
    },
    {
        "upstream_path": "content/en/docs/tasks/configure-pod-container/pull-image-private-registry.md",
        "local_filename": "pull-image-private-registry.md",
        "category": "Pod & Container Configuration",
    },
    {
        "upstream_path": "content/en/docs/tasks/configure-pod-container/quality-service-pod.md",
        "local_filename": "quality-service-pod.md",
        "category": "Pod & Container Configuration",
    },
    {
        "upstream_path": "content/en/docs/tasks/configure-pod-container/configure-pod-configmap.md",
        "local_filename": "configure-pod-configmap.md",
        "category": "Pod & Container Configuration",
    },
    {
        "upstream_path": "content/en/docs/tasks/administer-cluster/safely-drain-node.md",
        "local_filename": "safely-drain-node.md",
        "category": "Cluster Administration & Diagnostics",
    },
    {
        "upstream_path": "content/en/docs/tasks/administer-cluster/dns-debugging-resolution.md",
        "local_filename": "dns-debugging-resolution.md",
        "category": "Cluster Administration & Diagnostics",
    },
    {
        "upstream_path": "content/en/docs/tasks/administer-cluster/reserve-compute-resources.md",
        "local_filename": "reserve-compute-resources.md",
        "category": "Cluster Administration & Diagnostics",
    },
]


def extract_title_and_normalize(raw_content: str, default_title: str) -> Tuple[str, str]:
    """Extract document title from YAML front matter or header, then strip Hugo wrappers cleanly."""
    title = default_title
    lines = raw_content.splitlines()

    # Parse YAML front matter title
    if lines and lines[0].strip() == "---":
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
        if end_idx != -1:
            front_matter = lines[1:end_idx]
            for fm_line in front_matter:
                if fm_line.strip().startswith("title:"):
                    raw_t = fm_line.split(":", 1)[1].strip()
                    title = raw_t.strip("\"'")
                    break
            lines = lines[end_idx + 1 :]

    content = "\n".join(lines).strip()

    # Remove Hugo shortcodes like {{< note >}}, {{< /note >}}, {{% %}}, etc.
    content = re.sub(r"\{\{[%<]\s*/?[\w\s\-\".=]+\s*[%>]\}\}", "", content)

    # Ensure document starts with a top-level # title header if not present
    if not content.startswith("# "):
        content = f"# {title}\n\n{content}"

    return title, content


def extract_title_from_content(content: str, default_title: str) -> str:
    """Extract first top-level header title from normalized content."""
    for line in content.splitlines():
        line_str = line.strip()
        if line_str.startswith("# "):
            return line_str[2:].strip()
    return default_title


def compute_sha256(content: str) -> str:
    """Calculate SHA-256 hash of UTF-8 encoded string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def fetch_upstream_document(doc_entry: Dict[str, str], snapshot_dir: Path) -> Dict[str, Any]:
    """Fetch raw markdown file from GitHub commit URL or read existing local file if present."""
    upstream_path = doc_entry["upstream_path"]
    local_filename = doc_entry["local_filename"]
    url = f"https://raw.githubusercontent.com/kubernetes/website/{SOURCE_COMMIT}/{upstream_path}"
    local_file = snapshot_dir / "documents" / local_filename

    if local_file.exists():
        normalized_content = local_file.read_text(encoding="utf-8")
        title = extract_title_from_content(normalized_content, local_filename.rsplit(".", 1)[0])
    else:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP status {resp.status} when fetching {url}")
                raw_content = resp.read().decode("utf-8")
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch '{upstream_path}' from upstream: {exc}") from exc

        title, normalized_content = extract_title_and_normalize(raw_content, local_filename.rsplit(".", 1)[0])
        local_file.write_text(normalized_content, encoding="utf-8")

    doc_sha256 = compute_sha256(normalized_content)

    return {
        "local_path": f"documents/{local_filename}",
        "upstream_path": upstream_path,
        "source_url": url,
        "title": title,
        "category": doc_entry["category"],
        "sha256": doc_sha256,
        "content": normalized_content,
    }


def verify_manifest_integrity(snapshot_dir: Path) -> bool:
    """Verify committed local snapshot files against manifest.json hashes."""
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"Error: Manifest file '{manifest_path}' missing.", file=sys.stderr)
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    doc_list = manifest.get("documents", [])
    if len(doc_list) != len(DOCUMENT_ALLOWLIST):
        print(f"Error: Manifest declares {len(doc_list)} docs, expected {len(DOCUMENT_ALLOWLIST)}.", file=sys.stderr)
        return False

    all_valid = True
    for item in doc_list:
        file_p = snapshot_dir / item["local_path"]
        if not file_p.exists():
            print(f"Error: Local file '{file_p}' missing.", file=sys.stderr)
            all_valid = False
            continue
        content = file_p.read_text(encoding="utf-8")
        calc_hash = compute_sha256(content)
        if calc_hash != item["sha256"]:
            print(f"Error: Hash mismatch for '{item['local_path']}'. Manifest: {item['sha256']}, Calculated: {calc_hash}", file=sys.stderr)
            all_valid = False

    if all_valid:
        print(f"Success: Verified {len(doc_list)} snapshot documents against manifest SHA-256 hashes.")
    return all_valid


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch or verify frozen Kubernetes v1.31 KB snapshot.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/kb_snapshot",
        help="Target base directory for snapshot (default: data/kb_snapshot).",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing snapshot documents against manifest without downloading.",
    )
    args = parser.parse_args()

    snapshot_dir = Path(args.output_dir)

    if args.verify_only:
        ok = verify_manifest_integrity(snapshot_dir)
        sys.exit(0 if ok else 1)

    print(f"Fetching {len(DOCUMENT_ALLOWLIST)} documents from kubernetes/website @ tag '{SOURCE_TAG}' ({SOURCE_COMMIT})...")
    docs_dir = snapshot_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    fetched_records: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {executor.submit(fetch_upstream_document, entry, snapshot_dir): entry for entry in DOCUMENT_ALLOWLIST}
        for future in as_completed(future_map):
            entry = future_map[future]
            try:
                res = future.result()
                local_file = snapshot_dir / res["local_path"]
                local_file.write_text(res["content"], encoding="utf-8")
                print(f"  [OK] Fetched: {res['local_path']} ({len(res['content'])} bytes, SHA-256: {res['sha256'][:10]}...)")
                fetched_records.append({
                    "local_path": res["local_path"],
                    "upstream_path": res["upstream_path"],
                    "source_url": res["source_url"],
                    "title": res["title"],
                    "category": res["category"],
                    "sha256": res["sha256"],
                })
            except Exception as exc:
                print(f"  [FAIL] Failed fetching '{entry['upstream_path']}': {exc}", file=sys.stderr)
                sys.exit(1)

    # Sort manifest items by local_path for deterministic manifest ordering
    fetched_records.sort(key=lambda x: x["local_path"])

    manifest_data = {
        "corpus_name": "kubernetes-troubleshooting-v1.31",
        "source_repository": SOURCE_REPOSITORY,
        "source_tag": SOURCE_TAG,
        "source_commit": SOURCE_COMMIT,
        "kubernetes_version": KUBERNETES_VERSION,
        "document_count": len(fetched_records),
        "snapshot_purpose": "deliberately stale local KB for Corrective RAG",
        "license": LICENSE,
        "documents": fetched_records,
    }

    manifest_path = snapshot_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"\nSnapshot successfully created at '{snapshot_dir}'. Manifest written to '{manifest_path}'.")


if __name__ == "__main__":
    main()
