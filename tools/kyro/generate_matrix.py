#!/usr/bin/env python3
"""
Adaptive build matrix generator for DimToggle.
Generates an optimized GitHub Actions matrix from targets.json.
Groups targets by JDK/Gradle version family to maximize Gradle daemon reuse,
minimize wrapper downloads, eliminate redundant toolchain initialization,
and balance workloads across all 18 batches.
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def load_targets():
    data = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))
    entries = []
    for t in data["targets"]:
        mc = t["minecraft"]
        java_ver = t.get("java", 21)
        for loader in t["loaders"]:
            entries.append({
                "mc": mc,
                "loader": loader,
                "java": java_ver
            })
    return entries

def detect_self_hosted_runners():
    repo = os.environ.get("GITHUB_REPOSITORY", "KyroXova/DimToggle")
    runners_data = []
    import shutil
    import subprocess  # nosec B404
    gh_bin = shutil.which("gh")
    if gh_bin:
        try:
            res = subprocess.run(
                [gh_bin, "api", f"repos/{repo}/actions/runners", "--jq", ".runners"],
                capture_output=True, text=True, timeout=8, shell=False, check=False
            )  # nosec B603
            if res.returncode == 0 and res.stdout.strip():
                runners_data = json.loads(res.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as exc:
            print(f"Notice: gh runner detection unavailable: {exc}", file=sys.stderr)

    online_kyro_runners = []
    for r in runners_data:
        if r.get("status") == "online":
            labels = [lbl.get("name", "").lower() for lbl in r.get("labels", [])]
            name = r.get("name", "").lower()
            if "kyro" in labels or "docker" in labels or "dimtoggle" in name:
                online_kyro_runners.append(r)

    return online_kyro_runners

def generate(mode="auto", batches=18):
    targets = load_targets()
    online_runners = detect_self_hosted_runners()
    num_online = len(online_runners)
    print(f"Discovered {len(targets)} targets. Detected {num_online} online self-hosted runner(s).", file=sys.stderr)

    total = len(targets)
    if batches <= 0 or batches > total:
        batches = min(18, total)

    # Contiguous version slicing to keep Gradle wrapper + JDK + Minecraft assets warm
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

        # Runner selection logic
        if mode == "all-local":
            if num_online > 0:
                runner = ["self-hosted", "linux", "x64", "docker", "kyro"]
            else:
                print("Warning: all-local requested but no self-hosted runners online; falling back to ubuntu-24.04", file=sys.stderr)
                runner = "ubuntu-24.04"
        elif mode == "all-github" or num_online == 0:
            runner = "ubuntu-24.04"
        else:
            # Adaptive mode: Allocate up to 2 concurrent jobs per online VM
            self_hosted_slots = min(num_online * 2, batches // 2)
            if b_idx < self_hosted_slots:
                runner = ["self-hosted", "linux", "x64", "docker", "kyro"]
            else:
                runner = "ubuntu-24.04"

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
    parser = argparse.ArgumentParser(description="Generate adaptive GitHub Actions matrix with load balancing")
    parser.add_argument("--mode", choices=["auto", "all-github", "all-local"], default="auto")
    parser.add_argument("--batches", type=int, default=18, help="Number of balanced batches (default: 18)")
    parser.add_argument("--output-file", type=str, default=None)
    args = parser.parse_args()

    matrix = generate(mode=args.mode, batches=args.batches)
    matrix_json = json.dumps(matrix)

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output and os.path.exists(gh_output):
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"matrix={matrix_json}\n")
            f.write(f"total_batches={len(matrix['include'])}\n")
        print(f"Emitted balanced matrix with {len(matrix['include'])} batches to $GITHUB_OUTPUT", file=sys.stderr)
    elif args.output_file:
        Path(args.output_file).write_text(matrix_json, encoding="utf-8")
        print(f"Wrote matrix to {args.output_file}", file=sys.stderr)
    else:
        print(matrix_json)

if __name__ == "__main__":
    main()
