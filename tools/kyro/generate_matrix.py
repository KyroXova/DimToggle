#!/usr/bin/env python3
"""
Dynamic build matrix generator for DimToggle.
Generates an optimized GitHub Actions matrix from targets.json,
dynamically grouping targets into balanced batches to reuse VMs
and stay strictly under the 20 concurrent job limit.
"""

import json
import os
import sys
import random
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def load_targets():
    data = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))
    entries = []
    for t in data["targets"]:
        mc = t["minecraft"]
        java_ver = t.get("java", 21)
        for loader in t["loaders"].keys():
            entries.append({
                "mc": mc,
                "loader": loader,
                "java": java_ver
            })
    return entries

def count_self_hosted_runners():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "KyroXova/DimToggle")
    if not token:
        import shutil, subprocess
        if shutil.which("gh"):
            try:
                res = subprocess.run(
                    ["gh", "api", f"repos/{repo}/actions/runners", "--jq", ".runners | map(select(.status == \"online\")) | length"],
                    capture_output=True, text=True, timeout=10
                )
                if res.returncode == 0 and res.stdout.strip().isdigit():
                    return int(res.stdout.strip())
            except Exception:
                pass
        return 0

    import urllib.request
    url = f"https://api.github.com/repos/{repo}/actions/runners"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "DimToggle-Matrix-Generator"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            runners = data.get("runners", [])
            online = sum(1 for r in runners if r.get("status") == "online")
            return online
    except Exception as e:
        print(f"Notice: Could not query GitHub runners API: {e}", file=sys.stderr)
        return 0

def generate(mode="auto", batches=18, gh_share=20):
    targets = load_targets()
    online_self_hosted = count_self_hosted_runners()
    print(f"Discovered {len(targets)} targets in targets.json. Online self-hosted runners: {online_self_hosted}", file=sys.stderr)

    total = len(targets)
    if batches <= 0 or batches > total:
        batches = min(18, total)

    chunks = []
    start = 0
    for b in range(batches):
        size = total // batches + (1 if b < total % batches else 0)
        chunk = targets[start:start + size]
        start += size
        chunks.append(chunk)

    matrix_include = []
    for b_idx, chunk in enumerate(chunks):
        batch_id = f"batch-{b_idx + 1:02d}"
        mc_first = chunk[0]["mc"]
        mc_last = chunk[-1]["mc"]
        name = f"Batch {b_idx + 1:02d} ({mc_first} - {mc_last})" if mc_first != mc_last else f"Batch {b_idx + 1:02d} ({mc_first})"
        
        has_1_17 = any(t["mc"] in ("1.17", "1.17.1") for t in chunk)
        tasks_list = [f"build_{t['mc'].replace('.', '_')}_{t['loader']}" for t in chunk]
        tasks_str = " ".join(tasks_list)
        summary = ", ".join([f"{t['mc']} ({t['loader']})" for t in chunk])

        if mode == "all-local" and online_self_hosted > 0:
            runner = ["self-hosted", "linux", "x64", "docker", "kyro"]
        elif mode == "all-github" or online_self_hosted == 0:
            runner = "ubuntu-24.04"
        else:
            if b_idx < gh_share:
                runner = "ubuntu-24.04"
            else:
                runner = ["self-hosted", "linux", "x64", "docker", "kyro"]

        matrix_include.append({
            "batch_id": batch_id,
            "name": name,
            "tasks": tasks_str,
            "targets_summary": summary,
            "has_1_17": has_1_17,
            "count": len(chunk),
            "runner": runner
        })

    return {"include": matrix_include}

def main():
    parser = argparse.ArgumentParser(description="Generate dynamic GitHub Actions matrix with batching")
    parser.add_argument("--mode", choices=["auto", "all-github", "all-local", "split"], default="auto")
    parser.add_argument("--batches", type=int, default=18, help="Number of balanced batches (default: 18, range 16-20)")
    parser.add_argument("--gh-share", type=int, default=20, help="Number of batches assigned to GitHub cloud runners (default: 20)")
    parser.add_argument("--output-file", type=str, default=None)
    args = parser.parse_args()

    matrix = generate(mode=args.mode, batches=args.batches, gh_share=args.gh_share)
    matrix_json = json.dumps(matrix)

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output and os.path.exists(gh_output):
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"matrix={matrix_json}\n")
            f.write(f"total_batches={len(matrix['include'])}\n")
        print(f"Emitted matrix with {len(matrix['include'])} batches to $GITHUB_OUTPUT", file=sys.stderr)
    elif args.output_file:
        Path(args.output_file).write_text(matrix_json, encoding="utf-8")
        print(f"Wrote matrix to {args.output_file}", file=sys.stderr)
    else:
        print(matrix_json)

if __name__ == "__main__":
    main()
