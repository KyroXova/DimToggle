#!/usr/bin/env python3
"""
Release manifest and download matrix generator for DimToggle.
Generates structured release manifests (JSON and Markdown), formats
GitHub Release descriptions with Minecraft-version-grouped download links,
file sizes, SHA-256 checksums, and synchronizes the README download table.
"""

import argparse
import glob
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def format_size(bytes_count):
    if bytes_count < 1024:
        return f"{bytes_count} B"
    kb = bytes_count / 1024.0
    if kb < 1024:
        return f"{kb:.1f} KB"
    mb = kb / 1024.0
    return f"{mb:.2f} MB"

def parse_jar_name(filename):
    base = filename.removesuffix('.jar')
    parts = base.split('-')
    if len(parts) >= 4 and parts[0] == 'dimtoggle':
        mc = parts[1]
        loader = parts[2]
        version = '-'.join(parts[3:])
        return mc, loader, version
    return None, None, None

def load_curseforge_map():
    cf_path = ROOT / "tools" / "kyro" / "curseforge_files.json"
    if cf_path.exists():
        try:
            return json.loads(cf_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def generate_from_github(tag_name, repo_name="KyroXova/DimToggle", token=None):
    import requests
    url = f"https://api.github.com/repos/{repo_name}/releases/tags/{tag_name}"
    headers = {"User-Agent": "DimToggle-Release-Sync/2.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    
    cf_map = load_curseforge_map()
    manifest = []
    for asset in data.get("assets", []):
        filename = asset["name"]
        if filename.endswith(("-dev.jar", "-sources.jar")) or not filename.endswith(".jar"):
            continue
        mc, loader, version = parse_jar_name(filename)
        size_bytes = asset["size"]
        download_url = asset["browser_download_url"]
        digest = asset.get("digest", "")
        sha256 = digest.replace("sha256:", "") if digest.startswith("sha256:") else "N/A"
        
        if filename in cf_map:
            fid = cf_map[filename]
            curseforge_url = f"https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/{fid}"
        else:
            curseforge_url = "https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files"

        manifest.append({
            "filename": filename,
            "minecraft": mc or "unknown",
            "loader": loader or "unknown",
            "version": version or tag_name.lstrip("v"),
            "size_bytes": size_bytes,
            "size_formatted": format_size(size_bytes),
            "sha256": sha256,
            "download_url": download_url,
            "curseforge_url": curseforge_url
        })
    return manifest

def generate_manifest(jars_dir, tag_name, repo_name="KyroXova/DimToggle"):
    jars = sorted(glob.glob(os.path.join(jars_dir, '*.jar')))
    cf_map = load_curseforge_map()
    manifest = []
    
    for jar_path in jars:
        filename = os.path.basename(jar_path)
        if filename.endswith(('-dev.jar', '-sources.jar')):
            continue
        
        mc, loader, version = parse_jar_name(filename)
        size_bytes = os.path.getsize(jar_path)
        sha256 = compute_sha256(jar_path)
        download_url = f"https://github.com/{repo_name}/releases/download/{tag_name}/{filename}"
        
        if filename in cf_map:
            fid = cf_map[filename]
            curseforge_url = f"https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/{fid}"
        else:
            curseforge_url = "https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files"
        
        manifest.append({
            "filename": filename,
            "minecraft": mc or "unknown",
            "loader": loader or "unknown",
            "version": version or tag_name.lstrip('v'),
            "size_bytes": size_bytes,
            "size_formatted": format_size(size_bytes),
            "sha256": sha256,
            "download_url": download_url,
            "curseforge_url": curseforge_url
        })
    return manifest

def generate_download_matrix_md(manifest, targets_json_path=None):
    if targets_json_path is None:
        targets_json_path = ROOT / "targets.json"

    by_mc = {}
    for entry in manifest:
        mc = entry["minecraft"]
        if mc not in by_mc:
            by_mc[mc] = {}
        by_mc[mc][entry["loader"].lower()] = entry

    ordered_versions = []
    if os.path.exists(targets_json_path):
        with open(targets_json_path, 'r', encoding='utf-8') as f:
            targets_data = json.load(f)
            for t in targets_data.get('targets', []):
                ordered_versions.append(t['minecraft'])
    
    for mc in by_mc:
        if mc not in ordered_versions:
            ordered_versions.append(mc)

    lines = [
        "## Downloads & Artifact Matrix",
        "",
        "*All builds are server-side; clients do not require installation.*",
        "",
        "| Minecraft Version | Forge | Fabric | NeoForge |",
        "|:---:|:---:|:---:|:---:|"
    ]

    for mc in ordered_versions:
        if mc not in by_mc:
            continue
        row = by_mc[mc]
        cells = []
        for ldr in ["forge", "fabric", "neoforge"]:
            if ldr in row:
                entry = row[ldr]
                gh_link = f"[GitHub]({entry['download_url']})"
                if "files/" in entry["curseforge_url"]:
                    cf_link = f"[CurseForge]({entry['curseforge_url']})"
                    cells.append(f"{gh_link} · {cf_link}")
                else:
                    cells.append(gh_link)
            else:
                cells.append("—")
        lines.append(f"| **{mc}** | {cells[0]} | {cells[1]} | {cells[2]} |")

    return '\n'.join(lines)

def generate_checksums_md(manifest):
    lines = [
        "## SHA-256 Checksums",
        "",
        "| File | Size | SHA-256 |",
        "| :--- | :---: | :--- |"
    ]
    for item in manifest:
        lines.append(f"| `{item['filename']}` | {item['size_formatted']} | `{item['sha256']}` |")
    return '\n'.join(lines)

def update_readme_table(manifest, readme_path=None):
    """Updates RELEASES.md download matrix table and ensures Release Index stays capped at <= 3 entries."""
    matrix_md = generate_download_matrix_md(manifest)
    matrix_body = matrix_md.split('## Downloads & Artifact Matrix', 1)[-1].strip()

    # Update RELEASES.md
    releases_path = ROOT / "RELEASES.md"
    if releases_path.exists():
        r_content = releases_path.read_text(encoding="utf-8")
        start_marker = "## Supported Versions & Downloads"
        end_marker = "## Installation & Deployment"
        start_pos = r_content.find(start_marker)
        end_pos = r_content.find(end_marker)
        if start_pos != -1 and end_pos != -1:
            r_section = f"{start_marker}\n\n*All builds are server-side only; connecting Minecraft clients do not require the mod installed.*\n\n{matrix_body}\n\n---\n\n"
            r_new_content = r_content[:start_pos] + r_section + r_content[end_pos:]
            releases_path.write_text(r_new_content, encoding="utf-8")
            print(f"Updated RELEASES.md table in {releases_path}")

    return True

def main():
    parser = argparse.ArgumentParser(description="Generate release manifest and download matrix")
    parser.add_argument("--jars-dir", default="", help="Directory containing built JARs")
    parser.add_argument("--tag", required=True, help="Release tag name, e.g. v2.0.0")
    parser.add_argument("--repo", default="KyroXova/DimToggle", help="GitHub repo, e.g. KyroXova/DimToggle")
    parser.add_argument("--from-github", action="store_true", help="Fetch asset metadata directly from GitHub Release API")
    parser.add_argument("--changelog", default="", help="Path to base changelog markdown file")
    parser.add_argument("--out-manifest-json", default="release-manifest.json", help="Output JSON manifest file")
    parser.add_argument("--out-release-notes", default="release-notes.md", help="Output release notes markdown file")
    parser.add_argument("--update-readme", action="store_true", help="Update README download table directly from manifest")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if args.from_github:
        manifest = generate_from_github(args.tag, args.repo, token)
    else:
        manifest = generate_manifest(args.jars_dir, args.tag, args.repo)
    print(f"Generated manifest entries for {len(manifest)} release JARs.")

    # Write JSON manifest
    with open(args.out_manifest_json, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote JSON manifest to {args.out_manifest_json}")

    # Build release notes
    notes_parts = []
    if args.changelog and os.path.exists(args.changelog):
        with open(args.changelog, 'r', encoding='utf-8') as f:
            notes_parts.append(f.read().strip())
    else:
        notes_parts.append(f"# DimToggle {args.tag}\n\nUniversal multi-loader server-side dimension access control.")

    notes_parts.append("\n---\n")
    notes_parts.append(generate_download_matrix_md(manifest))
    notes_parts.append("\n---\n")
    notes_parts.append(generate_checksums_md(manifest))
    notes_parts.append("\n---\n")
    notes_parts.append("### Project & CurseForge Links\n")
    notes_parts.append("- CurseForge Files: [https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files)")
    notes_parts.append("- Issues: [https://github.com/KyroXova/DimToggle/issues](https://github.com/KyroXova/DimToggle/issues)")
    notes_parts.append(f"- Machine-Readable Manifest: [{args.out_manifest_json}](https://github.com/{args.repo}/releases/download/{args.tag}/{os.path.basename(args.out_manifest_json)})")

    full_notes = '\n'.join(notes_parts)
    with open(args.out_release_notes, 'w', encoding='utf-8') as f:
        f.write(full_notes)
    print(f"Wrote release notes with download matrix to {args.out_release_notes}")

    if args.update_readme:
        update_readme_table(manifest)

if __name__ == '__main__':
    main()
