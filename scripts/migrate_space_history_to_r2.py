#!/usr/bin/env python3
"""Validated, non-destructive migration of indexed private Space history to R2."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE_RE = re.compile(r"history/(?:run-([0-9]{7,15})|legacy-([0-9]{14}))\.json")
PRESERVE_FILES = ("search-history.json", "jobs.json", "seen-jobs.json",
                  "index.html", "frontend-v3.js", "frontend-v3.css")

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def validate_index(index: dict, actual: dict[str, int]) -> list[dict]:
    if not isinstance(index, dict) or not isinstance(index.get("runs"), list):
        raise ValueError("search-history.json must contain a runs array")
    rows, seen_ids, seen_paths = [], set(), set()
    for row in index["runs"]:
        if not isinstance(row, dict) or row.get("published") is not True:
            continue
        run_id = str(row.get("run_id") or "")
        path = row.get("archive_file")
        match = ARCHIVE_RE.fullmatch(path or "")
        if not match:
            raise ValueError("Invalid indexed archive path")
        if path in seen_paths or run_id in seen_ids:
            raise ValueError("Duplicate archive path or run ID in history index")
        if match.group(1) and run_id != match.group(1):
            raise ValueError("Index run ID does not match archive filename")
        if path not in actual:
            raise ValueError("Indexed archive missing from Space: " + path)
        seen_paths.add(path); seen_ids.add(run_id)
        rows.append({"run_id": run_id, "archive_file": path, "index_row": row})
    if not rows:
        raise ValueError("No published history archives; refusing empty migration")
    extras = set(actual) - seen_paths
    if extras:
        raise ValueError("Unindexed history archives found: " + ", ".join(sorted(extras)))
    if seen_paths != set(actual):
        raise ValueError("Space history inventory and published index differ")
    return rows

def build_manifest(space: str, index_raw: bytes, entries: list[dict],
                   preserved: list[dict], generated_at: str,
                   r2_snapshot_files: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "migration": "space-history-to-r2",
        "artifact_type": "migration_manifest",
        "source_space": space,
        "generated_at": generated_at,
        "history_index": {"path": "search-history.json", "bytes": len(index_raw),
                          "sha256": sha256(index_raw), "published_archive_count": len(entries)},
        "archives": entries,
        "r2_snapshot_files": r2_snapshot_files or [],
        "preserved_space_files": preserved,
        "deletion_performed": False,
    }

def request_bytes(url: str, method: str, token: str, raw: bytes | None = None) -> bytes:
    headers = {"X-Archive-CI-Token": token,
               "X-Dashboard-Key": os.environ.get("DASHBOARD_API_KEY", "").strip()}
    if raw is not None: headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=raw, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("HF_TOKEN", "").strip()
    space = os.environ.get("HF_SPACE_ID", "").strip()
    bridge = os.environ.get("BRIDGE_URL", "https://career-radar-bridge.happytiswis.workers.dev").strip().rstrip("/")
    ci_token = os.environ.get("ARCHIVE_CI_TOKEN", "").strip()
    dashboard_key = os.environ.get("DASHBOARD_API_KEY", "").strip()
    if not token or not space: raise SystemExit("HF_TOKEN and HF_SPACE_ID are required")
    if not args.dry_run and (not ci_token or not dashboard_key):
        raise SystemExit("ARCHIVE_CI_TOKEN and DASHBOARD_API_KEY are required for live migration")
    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi(token=token)
    index_path = Path(hf_hub_download(repo_id=space, filename="search-history.json", repo_type="space", token=token))
    index_raw = index_path.read_bytes()
    index = json.loads(index_raw)
    tree = api.list_repo_tree(repo_id=space, repo_type="space", path_in_repo="history", recursive=True, expand=False)
    actual = {e.path: int(e.size) for e in tree if getattr(e, "path", None) and ARCHIVE_RE.fullmatch(e.path)}
    rows = validate_index(index, actual)
    objects, archive_manifest, total = [], [], 0
    for row in rows:
        path = row["archive_file"]
        raw = Path(hf_hub_download(repo_id=space, filename=path, repo_type="space", token=token)).read_bytes()
        if len(raw) != actual[path]: raise ValueError("Source size mismatch: " + path)
        doc = json.loads(raw)
        match = ARCHIVE_RE.fullmatch(path)
        if match.group(1) and str(doc.get("run_id") or "") != match.group(1):
            raise ValueError("Embedded run ID mismatch: " + path)
        digest = sha256(raw); total += len(raw)
        objects.append((path, raw, digest))
        archive_manifest.append({
            "run_id": row["run_id"], "path": path, "bytes": len(raw), "sha256": digest,
            "run_url": row["index_row"].get("run_url"),
            "published_at": row["index_row"].get("published_at"),
        })
    preserved, snapshot_objects, snapshot_manifest = [], [], []
    snapshot_paths = {"search-history.json", "jobs.json", "seen-jobs.json"}
    for path in PRESERVE_FILES:
        local = Path(hf_hub_download(repo_id=space, filename=path, repo_type="space", token=token))
        raw = local.read_bytes()
        digest = sha256(raw)
        if path in snapshot_paths:
            try:
                parsed = json.loads(raw)
            except Exception as exc:
                raise ValueError("Preserved JSON file is invalid: " + path) from exc
            if path == "search-history.json" and not isinstance(parsed.get("runs") if isinstance(parsed, dict) else None, list):
                raise ValueError("Preserved search-history.json has no runs array")
            if path == "jobs.json":
                if not isinstance(parsed, dict) or not isinstance(parsed.get("run_id"), (str, int)) or not parsed.get("generated_at"):
                    raise ValueError("Preserved jobs.json dashboard snapshot is missing run_id or generated_at")
                if not isinstance(parsed.get("total_shortlisted"), int):
                    raise ValueError("Preserved jobs.json dashboard snapshot has no total_shortlisted count")
            if path == "seen-jobs.json" and not isinstance(parsed, (dict, list)):
                raise ValueError("Preserved seen-jobs.json has an unsupported root type")
        preserved.append({"path": path, "bytes": len(raw), "sha256": digest, "preserved_in_space": True})
        if path in snapshot_paths:
            snapshot_objects.append((path, raw, digest))
            snapshot_manifest.append({"path": path, "bytes": len(raw), "sha256": digest,
                                      "preserved_in_space": True, "stored_in_r2": True})
    if {path for path, _, _ in snapshot_objects} != snapshot_paths:
        raise ValueError("Latest dashboard snapshot, history index or seen-jobs registry is missing")
    generated = datetime.now(timezone.utc).isoformat()
    manifest = build_manifest(space, index_raw, archive_manifest, preserved, generated, snapshot_manifest)
    manifest_raw = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    manifest_key = "history/legacy-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + ".json"
    print(json.dumps({"validated_archives": len(objects), "archive_bytes": total,
                      "r2_snapshot_files": len(snapshot_objects),
                      "preserved_files": len(preserved), "manifest_key": manifest_key,
                      "manifest_sha256": sha256(manifest_raw), "dry_run": args.dry_run}))
    if args.dry_run:
        print("DRY RUN: no R2 writes; no Space files changed.")
        return 0
    upload_objects = objects + snapshot_objects
    for key, raw, digest in upload_objects:
        result = json.loads(request_bytes(bridge + "/archives?key=" + urllib.parse.quote(key, safe=""),
                                          "PUT", ci_token, raw))
        if not result.get("stored") or int(result.get("size") or 0) != len(raw):
            raise RuntimeError("Bridge did not confirm exact upload size: " + key)
    result = json.loads(request_bytes(bridge + "/archives?key=" + urllib.parse.quote(manifest_key, safe=""),
                                      "PUT", ci_token, manifest_raw))
    if not result.get("stored") or int(result.get("size") or 0) != len(manifest_raw):
        raise RuntimeError("Bridge did not confirm manifest upload")
    for key, raw, digest in upload_objects + [(manifest_key, manifest_raw, sha256(manifest_raw))]:
        stored = request_bytes(bridge + "/archives/" + key, "GET", ci_token)
        if len(stored) != len(raw) or sha256(stored) != digest:
            raise RuntimeError("R2 SHA-256 read-back failed: " + key)
        print("SHA-256 verified: " + key)
    print("SUCCESS: all indexed archives, latest jobs.json snapshot, search-history.json, seen-jobs.json and manifest verified in R2. Space files remain unchanged.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise
