#!/usr/bin/env python3
"""
Adaptive build matrix generator for DimToggle.
Generates an optimized GitHub Actions matrix from targets.json using
historical execution profiles and dynamic self-hosted runner detection.
Balances expensive Forge/NeoForge and lightweight Fabric targets across
batches to eliminate workload imbalance and minimize CI completion time.
"""

import os
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Historical target weights in seconds derived from CI profiling
WEIGHT_BASE_FABRIC = 35.0
WEIGHT_BASE_FORGE = 75.0
WEIGHT_BASE_NEOFORGE = 110.0

WEIGHT_JAVA_8 = 15.0     # Gradle 6/7 daemon start + legacy Forge
WEIGHT_JAVA_16 = 30.0    # Zulu 16 download & environment switch
WEIGHT_JAVA_17 = 10.0
WEIGHT_JAVA_21 = 15.0

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

def compute_target_weight(target):
    loader = target["loader"].lower()
    java_ver = target["java"]
    mc = target["mc"]

    if loader == "neoforge":
        w = WEIGHT_BASE_NEOFORGE
    elif loader == "forge":
        w = WEIGHT_BASE_FORGE
    else:
        w = WEIGHT_BASE_FABRIC

    if java_ver == 8:
        w += WEIGHT_JAVA_8
    elif java_ver == 16 or mc in ("1.17", "1.17.1"):
        w += WEIGHT_JAVA_16
    elif java_ver == 17:
        w += WEIGHT_JAVA_17
    else:
        w += WEIGHT_JAVA_21

    return w

def detect_self_hosted_runners():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "KyroXova/DimToggle")
    
    runners_data = []
    if token:
        import urllib.request
        url = f"https://api.github.com/repos/{repo}/actions/runners"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "DimToggle-Adaptive-Matrix"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                runners_data = data.get("runners", [])
        except Exception as e:
            print(f"Notice: Failed to fetch runners via GitHub API token: {e}", file=sys.stderr)
            
    if not runners_data:
        import shutil, subprocess
        if shutil.which("gh"):
            try:
                res = subprocess.run(
                    ["gh", "api", f"repos/{repo}/actions/runners", "--jq", ".runners"],
                    capture_output=True, text=True, timeout=8
                )
                if res.returncode == 0:
                    runners_data = json.loads(res.stdout)
            except Exception:
                pass

    online_kyro_runners = []
    for r in runners_data:
        if r.get("status") == "online":
            labels = [lbl.get("name", "").lower() for lbl in r.get("labels", [])]
            name = r.get("name", "").lower()
            if "kyro" in labels or "docker" in labels or "dimtoggle" in name:
                online_kyro_runners.append(r)

    return online_kyro_runners

def balance_workloads(targets, num_batches=18):
    # Group targets by Minecraft version family to preserve Gradle/Loom cache locality
    by_version = {}
    for t in targets:
        mc = t["mc"]
        if mc not in by_version:
            by_version[mc] = []
        by_version[mc].append(t)

    # Sort version clusters by descending total weight
    version_clusters = []
    for mc, cluster in by_version.items():
        total_w = sum(compute_target_weight(t) for t in cluster)
        version_clusters.append((mc, cluster, total_w))

    version_clusters.sort(key=lambda x: x[2], reverse=True)

    # Initialize bins
    bins = [{"id": i, "weight": 0.0, "targets": []} for i in range(num_batches)]

    for mc, cluster, cluster_weight in version_clusters:
        # Assign entire cluster to the bin with minimal weight
        # to preserve cache locality while balancing totals
        min_bin = min(bins, key=lambda b: b["weight"])
        min_bin["targets"].extend(cluster)
        min_bin["weight"] += cluster_weight

    # Sort targets inside each bin by Minecraft version according to original targets order
    mc_order = {t["mc"]: idx for idx, t in enumerate(targets)}
    for b in bins:
        b["targets"].sort(key=lambda t: (mc_order.get(t["mc"], 999), t["loader"]))

    # Sort bins chronologically by their first target's Minecraft version
    bins.sort(key=lambda b: mc_order.get(b["targets"][0]["mc"], 999) if b["targets"] else 0)
    return bins

def generate(mode="auto", batches=18):
    targets = load_targets()
    online_runners = detect_self_hosted_runners()
    num_online = len(online_runners)
    print(f"Discovered {len(targets)} targets. Detected {num_online} online self-hosted runner(s).", file=sys.stderr)

    if batches <= 0 or batches > len(targets):
        batches = min(18, len(targets))

    bins = balance_workloads(targets, num_batches=batches)

    matrix_include = []
    for b_idx, b in enumerate(bins):
        chunk = b["targets"]
        if not chunk:
            continue
            
        batch_id = f"batch-{b_idx + 1:02d}"
        mc_versions = sorted(list(set(t["mc"] for t in chunk)), key=lambda v: [int(x) for x in v.split(".") if x.isdigit()])
        mc_first = mc_versions[0]
        mc_last = mc_versions[-1]
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
            # Adaptive mode:
            # Allocate slots to online self-hosted runners proportional to concurrency (up to 2 per VM)
            # and remaining jobs to GitHub cloud runners
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
            "estimated_weight": round(b["weight"], 1),
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
