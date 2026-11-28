#!/usr/bin/env python3
"""
CI Analytics, Performance Profiler, and Adaptive Scheduler for DimToggle.
Analyzes historical successful GitHub Actions runs, measures target and batch
execution times, runner utilization, and produces optimal balanced schedules.
"""

import datetime
import json
import re
import shutil
import subprocess  # nosec B404
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUCCESSFUL_BUILD_RUNS = ["45325849440", "45196255150", "45193659512"]
CF_RELEASE_RUN = "45198269674"

def parse_iso(dt_str):
    if not dt_str:
        return None
    return datetime.datetime.fromisoformat(dt_str)

def fetch_run_data(run_id, repo="KyroXova/DimToggle"):
    safe_id = str(int(str(run_id).strip()))
    gh_bin = shutil.which("gh") or "gh"
    cmd = [gh_bin, "run", "view", safe_id, "--repo", repo, "--json", "jobs,status,conclusion,name,headSha,createdAt"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=False)  # nosec B603
    return json.loads(res.stdout)

def extract_curseforge_map(repo="KyroXova/DimToggle"):
    safe_id = str(int(CF_RELEASE_RUN.strip()))
    gh_bin = shutil.which("gh") or "gh"
    cmd = [gh_bin, "run", "view", safe_id, "--repo", repo, "--log"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=False)  # nosec B603
    pattern = re.compile(r"Uploaded\s+([\w\.\-]+?\.jar)\s+->\s+CurseForge response:\s*\{\"id\":(\d+)\}")
    matches = pattern.findall(res.stdout)
    cf_map = {}
    for jar, fid in matches:
        cf_map[jar] = fid
    
    out_path = ROOT / "tools" / "kyro" / "curseforge_files.json"
    out_path.write_text(json.dumps(cf_map, indent=2), encoding="utf-8")
    print(f"Extracted {len(cf_map)} CurseForge file mappings to {out_path}")
    return cf_map

def analyze_historical_runs():
    all_job_stats = {}
    
    for run_id in SUCCESSFUL_BUILD_RUNS:
        data = fetch_run_data(run_id)
        if data.get("conclusion") != "success":
            continue
        
        for job in data.get("jobs", []):
            name = job["name"]
            if name == "Generate Matrix":
                continue
            
            started = parse_iso(job.get("startedAt"))
            completed = parse_iso(job.get("completedAt"))
            if not (started and completed):
                continue
            
            dur = (completed - started).total_seconds()
            if name not in all_job_stats:
                all_job_stats[name] = []
            all_job_stats[name].append({
                "run_id": run_id,
                "duration": dur,
                "runner_name": job.get("runnerName", "unknown"),
                "runner_group": job.get("runnerGroupName", "unknown")
            })

    summary = {}
    for name, entries in sorted(all_job_stats.items()):
        durations = [e["duration"] for e in entries]
        avg_dur = sum(durations) / len(durations)
        min_dur = min(durations)
        max_dur = max(durations)
        summary[name] = {
            "avg_seconds": round(avg_dur, 1),
            "min_seconds": round(min_dur, 1),
            "max_seconds": round(max_dur, 1),
            "samples": len(durations),
            "runners": list({e["runner_name"] for e in entries})
        }

    return summary

def generate_report():
    print("Fetching and analyzing historical successful CI runs...")
    summary = analyze_historical_runs()
    
    print("\n=== CI Historical Execution Summary (Successful Runs Only) ===")
    print(f"{'Batch Name':<35} | {'Avg (s)':<8} | {'Min (s)':<8} | {'Max (s)':<8} | {'Samples':<7}")
    print("-" * 75)
    
    sorted_batches = sorted(summary.items(), key=lambda x: x[1]["avg_seconds"], reverse=True)
    for name, s in sorted_batches:
        print(f"{name:<35} | {s['avg_seconds']:<8.1f} | {s['min_seconds']:<8.1f} | {s['max_seconds']:<8.1f} | {s['samples']:<7}")
    
    total_avg = sum(s["avg_seconds"] for s in summary.values())
    max_batch = sorted_batches[0][1]["avg_seconds"]
    min_batch = sorted_batches[-1][1]["avg_seconds"]
    spread = max_batch - min_batch
    
    print("-" * 75)
    print(f"Slowest Batch Avg: {max_batch:.1f}s ({max_batch/60:.1f}m)")
    print(f"Fastest Batch Avg: {min_batch:.1f}s ({min_batch/60:.1f}m)")
    print(f"Workload Imbalance Spread: {spread:.1f}s ({spread/60:.1f}m)")
    print(f"Total Cumulative Work: {total_avg:.1f}s ({total_avg/60:.1f}m)")
    print(f"Theoretical Balanced Duration (18 batches): {total_avg/18:.1f}s ({total_avg/18/60:.1f}m)")

    # Also extract CurseForge mappings
    extract_curseforge_map()

if __name__ == "__main__":
    generate_report()
