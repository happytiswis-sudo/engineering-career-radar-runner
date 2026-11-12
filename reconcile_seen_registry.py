#!/usr/bin/env python3
"""Reconcile only the private seen-job registry from already published HF archives.

This operation does not run a source search, publish jobs.json, touch Supabase, or
delete history. It aborts without uploading when any indexed archive is missing
or fails its run-ID validation.
"""
from __future__ import annotations

import io
import json
import os
import re
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import EntryNotFoundError

from novelty import (
    merge_archive_registry,
    registry_from_archives,
    registry_needs_archive_rebuild,
)


ARCHIVE_PATTERN = re.compile(
    r"history/(?:run-[0-9]{7,15}|legacy-[0-9]{14})\.json"
)


def read_json(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object in " + path)
    return value


def main() -> None:
    token = os.environ.get("HF_TOKEN", "")
    space = os.environ.get("HF_SPACE_ID", "")
    if not token or not space:
        raise RuntimeError("Missing HF_TOKEN or HF_SPACE_ID")

    prior_path = hf_hub_download(
        repo_id=space,
        filename="search-history.json",
        repo_type="space",
        token=token,
    )
    prior = read_json(prior_path)
    rows = prior.get("runs")
    if not isinstance(rows, list):
        raise RuntimeError("Published history index has no valid runs array")

    archive_rows = [
        row for row in rows
        if isinstance(row, dict) and row.get("archive_file")
    ]
    limit = max(40, len(archive_rows))
    if not archive_rows:
        raise RuntimeError("No published archives are indexed; refusing to create an empty registry")

    try:
        seen_path = hf_hub_download(
            repo_id=space,
            filename="seen-jobs.json",
            repo_type="space",
            token=token,
        )
    except EntryNotFoundError:
        existing = None
    else:
        existing = read_json(seen_path)

    if not registry_needs_archive_rebuild(existing, prior, limit=limit):
        coverage = existing.get("coverage", {})
        print(
            "No reconciliation needed: registry already covers "
            + str(len(coverage.get("archive_run_ids", [])))
            + " indexed archives."
        )
        return

    def read_archive(name: str) -> dict:
        if not isinstance(name, str) or not ARCHIVE_PATTERN.fullmatch(name):
            raise ValueError("Unsafe historical archive path")
        local_path = hf_hub_download(
            repo_id=space,
            filename=name,
            repo_type="space",
            token=token,
        )
        return read_json(local_path)

    rebuilt = registry_from_archives(prior, read_archive, limit=limit)
    coverage = rebuilt.get("coverage", {})
    expected = coverage.get("expected_archive_run_ids", [])
    loaded = coverage.get("archive_run_ids", [])

    # All archive IDs in the current index must be loaded before the registry
    # is replaced. Preserve the existing registry unchanged on any gap.
    if not coverage.get("complete") or loaded != expected:
        raise RuntimeError(
            "Archive coverage incomplete; registry not uploaded. "
            + str(coverage.get("archives_loaded", 0))
            + " / "
            + str(coverage.get("archives_available", 0))
            + " archives loaded; errors="
            + str(coverage.get("errors", 0))
        )

    merged = merge_archive_registry(existing, rebuilt)
    payload = json.dumps(
        merged, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=io.BytesIO(payload),
        path_in_repo="seen-jobs.json",
        repo_id=space,
        repo_type="space",
        commit_message="Reconcile seen-job registry from published history archives",
    )

    # Verify the Hub copy after upload, not just the local in-memory object.
    verified_path = hf_hub_download(
        repo_id=space,
        filename="seen-jobs.json",
        repo_type="space",
        token=token,
        force_download=True,
    )
    verified = read_json(verified_path)
    verified_coverage = verified.get("coverage", {})
    if verified_coverage.get("archive_run_ids") != expected:
        raise RuntimeError("Uploaded registry coverage verification failed")
    if len(verified.get("entries", {})) != len(merged["entries"]):
        raise RuntimeError("Uploaded registry entry-count verification failed")

    recurring = sum(
        1 for row in verified["entries"].values()
        if int(row.get("count", 1)) > 1
    )
    location_variants = sum(
        1 for row in verified["entries"].values()
        if len(row.get("locations") or []) > 1
    )
    posting_date_variants = sum(
        1 for row in verified["entries"].values()
        if len(row.get("posting_dates") or []) > 1
    )
    requisition_id_variants = sum(
        1 for row in verified["entries"].values()
        if len(row.get("posting_ids") or []) > 1
    )
    print(
        "Registry reconciled and verified: "
        + str(len(expected))
        + " archives, "
        + str(len(verified["entries"]))
        + " identities, "
        + str(recurring)
        + " identities seen in multiple archived runs; "
        + str(location_variants)
        + " location variants; "
        + str(posting_date_variants)
        + " posting-date variants; "
        + str(requisition_id_variants)
        + " requisition-ID variants. Only seen-jobs.json was updated."
    )


if __name__ == "__main__":
    main()
