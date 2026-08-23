"""Offline snapshot integrity tests for frozen Kubernetes v1.31 Knowledge Base."""

import hashlib
import json
from pathlib import Path


def _get_snapshot_dir() -> Path:
    """Resolve workspace data/kb_snapshot directory relative to test file."""
    test_dir = Path(__file__).parent
    workspace_root = test_dir.parent.parent
    snapshot_dir = workspace_root / "data" / "kb_snapshot"
    return snapshot_dir


def test_manifest_existence_and_provenance() -> None:
    """Verify manifest.json exists, specifies v1.31 snapshot tag and commit SHA."""
    snapshot_dir = _get_snapshot_dir()
    manifest_path = snapshot_dir / "manifest.json"
    assert manifest_path.exists(), f"Manifest file missing at {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["source_repository"] == "https://github.com/kubernetes/website"
    assert manifest["source_tag"] == "snapshot-initial-v1.31"
    assert manifest["source_commit"] == "20d164c7a7d092ebc65eed06c855d2ec4f0f0e12"
    assert manifest["kubernetes_version"] == "1.31"
    assert manifest["license"] == "CC-BY-4.0"

    doc_count = manifest["document_count"]
    assert 30 <= doc_count <= 40
    assert doc_count == len(manifest["documents"])


def test_snapshot_document_count_and_uniqueness() -> None:
    """Verify snapshot document files match manifest and paths are unique."""
    snapshot_dir = _get_snapshot_dir()
    manifest_path = snapshot_dir / "manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    docs_dir = snapshot_dir / "documents"
    actual_files = list(docs_dir.glob("*.md"))
    assert len(actual_files) == manifest["document_count"]

    local_paths = [doc["local_path"] for doc in manifest["documents"]]
    upstream_paths = [doc["upstream_path"] for doc in manifest["documents"]]

    assert len(local_paths) == len(set(local_paths)), "Duplicate local_path in manifest"
    assert len(upstream_paths) == len(set(upstream_paths)), "Duplicate upstream_path in manifest"


def test_document_hash_integrity() -> None:
    """Verify every committed document file's SHA-256 matches manifest entry."""
    snapshot_dir = _get_snapshot_dir()
    manifest_path = snapshot_dir / "manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for item in manifest["documents"]:
        doc_file = snapshot_dir / item["local_path"]
        assert doc_file.exists(), f"Committed snapshot file missing: {doc_file}"

        content = doc_file.read_text(encoding="utf-8")
        calc_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert calc_sha == item["sha256"], f"Hash mismatch for {item['local_path']}"


def test_quantum_scheduler_flag_absence() -> None:
    """Verify fictional --enable-quantum-scheduler flag has zero occurrences in local corpus."""
    snapshot_dir = _get_snapshot_dir()
    docs_dir = snapshot_dir / "documents"
    search_term = "enable-quantum-scheduler"

    matches = []
    for doc_file in docs_dir.glob("*.md"):
        content = doc_file.read_text(encoding="utf-8").lower()
        if search_term in content:
            matches.append(doc_file.name)

    assert len(matches) == 0, f"Found unexpected matches for fake flag in: {matches}"


def test_golden_query_1_troubleshooting_coverage() -> None:
    """Verify corpus contains curated files covering Pod lifecycle & CrashLoopBackOff diagnostics."""
    snapshot_dir = _get_snapshot_dir()
    manifest_path = snapshot_dir / "manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    file_names = {Path(doc["local_path"]).name for doc in manifest["documents"]}

    expected_key_files = {
        "pod-lifecycle.md",
        "debug-pods.md",
        "debug-running-pod.md",
        "configure-liveness-readiness-startup-probes.md",
        "determine-reason-pod-failure.md",
    }

    assert expected_key_files.issubset(file_names), f"Missing expected troubleshooting files: {expected_key_files - file_names}"
