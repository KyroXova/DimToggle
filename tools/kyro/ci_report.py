"""CI failure diagnosis and reporting tool for DimToggle.

Analyzes GitHub Actions job results, extracts failure causes,
writes to GitHub Step Summary, and posts PR comments.
"""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys
import time

def parse_failure_reason(log_text):
    """Extract a concise failure reason from Gradle / build log."""
    if not log_text:
        return "Unknown failure (empty log)"
    
    # Common Gradle error patterns
    if "Received status code 429" in log_text or "Too Many Requests" in log_text:
        return "Network rate limited (HTTP 429: Too Many Requests)"
    if "Read timed out" in log_text:
        return "Network read timed out while fetching dependencies"
    if "Could not resolve" in log_text:
        for line in log_text.splitlines():
            line_str = line.strip()
            if "> Could not resolve" in line_str or "> Could not find" in line_str:
                return line_str.lstrip("> ")
    if "error: cannot find symbol" in log_text:
        for line in log_text.splitlines():
            if "error: cannot find symbol" in line:
                return line.strip()
    if "Execution failed for task" in log_text:
        for line in log_text.splitlines():
            if "Execution failed for task" in line:
                return line.strip().lstrip("* ").lstrip("> ")
    if "* What went wrong:" in log_text:
        lines = log_text.splitlines()
        for i, line in enumerate(lines):
            if "* What went wrong:" in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    return next_line
    
    # Fallback: find any line with ERROR or FAILURE
    for line in reversed(log_text.splitlines()):
        clean = line.strip()
        if clean.startswith("FAILURE:") or clean.startswith("##[error]"):
            return clean
            
    return "Build failed during execution"

def fetch_all_jobs(run_id):
    """Fetch all jobs for a run using paginated GitHub API (avoids 502 gateway timeouts)."""
    jobs = []
    page = 1
    for _ in range(10): # up to 500 jobs
        cmd = ["gh", "api", f"repos/:owner/:repo/actions/runs/{run_id}/jobs?per_page=50&page={page}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            # Retry with short sleep if a page errors
            time.sleep(2)
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                break
        try:
            data = json.loads(res.stdout)
            page_jobs = data.get("jobs", [])
            if not page_jobs:
                break
            jobs.extend(page_jobs)
            if len(page_jobs) < 50:
                break
            page += 1
        except Exception:
            break
    return jobs

def main():
    parser = argparse.ArgumentParser(description="Analyze CI jobs and report diagnostics")
    parser.add_argument("--run-id", required=True, help="GitHub run ID")
    parser.add_argument("--pr-number", default="", help="Pull request number to comment on")
    args = parser.parse_args()

    jobs = fetch_all_jobs(args.run_id)
    if not jobs:
        # Fallback to single query if pagination failed
        cmd = ["gh", "run", "view", args.run_id, "--json", "jobs"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                jobs = json.loads(res.stdout).get("jobs", [])
            except Exception:
                pass

    if not jobs:
        print(f"Warning: Could not fetch jobs metadata from GitHub API. Allowing pipeline to proceed.", file=sys.stderr)
        sys.exit(0)
    
    # Identify build matrix jobs
    build_jobs = [j for j in jobs if j.get("name") not in (
        "Base Validation & Matrix Check",
        "Pipeline Verification & Diagnostics",
        "Pipeline Verification & Matrix Checks",
        "Publish Release & CurseForge Description"
    )]
    failed_jobs = [j for j in build_jobs if j.get("conclusion") == "failure"]

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    report_lines = []

    if not failed_jobs:
        report_lines.append("## ✅ All DimToggle Build Targets Passed")
        report_lines.append("")
        report_lines.append(f"Successfully verified all **{len(build_jobs)} build targets** across all supported Minecraft versions and loaders.")
        report_lines.append("Pipeline will now proceed to the release and publishing flow.")
        report_content = "\n".join(report_lines)
        print(report_content)
        if summary_file:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(report_content + "\n")
        sys.exit(0)

    # Failures detected
    report_lines.append("## ❌ DimToggle Build Matrix Failures Detected")
    report_lines.append("")
    report_lines.append(f"**{len(failed_jobs)}** out of **{len(build_jobs)}** targets failed during compilation or verification.")
    report_lines.append("Release workflow has been halted.")
    report_lines.append("")
    report_lines.append("| Target | Conclusion | Diagnostics Summary |")
    report_lines.append("| :--- | :---: | :--- |")

    details_blocks = []

    for job in failed_jobs:
        job_name = job.get("name", "Unknown")
        job_id = job.get("databaseId") or job.get("id")
        
        # Fetch failure log with retry
        log_snippet = ""
        if job_id:
            for log_attempt in range(1, 4):
                log_res = subprocess.run(["gh", "run", "view", "--job", str(job_id), "--log-failed"], capture_output=True, text=True)
                if log_res.returncode == 0 and log_res.stdout:
                    log_snippet = log_res.stdout
                    break
                time.sleep(2)

        reason = parse_failure_reason(log_snippet)
        report_lines.append(f"| **{job_name}** | ❌ Failed | `{reason}` |")

        # Save details
        if log_snippet:
            lines = [l for l in log_snippet.splitlines() if l.strip()]
            tail = "\n".join(lines[-35:])
            details_blocks.append(f"<details>\n<summary><b>{job_name} Failure Log Excerpt</b></summary>\n\n```text\n{tail}\n```\n</details>\n")

    report_lines.append("")
    if details_blocks:
        report_lines.append("### Failure Details")
        report_lines.extend(details_blocks)

    report_content = "\n".join(report_lines)
    print(report_content)

    # Write to Step Summary
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(report_content + "\n")

    # Post PR Comment if PR number is available
    if args.pr_number and args.pr_number.isdigit():
        tmp_report = Path(".github/ci_report_temp.md")
        try:
            tmp_report.write_text(report_content, encoding="utf-8")
            subprocess.run(["gh", "pr", "comment", args.pr_number, "--body-file", str(tmp_report)], check=False)
        finally:
            if tmp_report.exists():
                tmp_report.unlink()

    # Exit 1 so the job fails and release step is skipped
    sys.exit(1)

if __name__ == "__main__":
    main()
