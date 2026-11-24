#!/usr/bin/env python3
"""
Release manifest and download matrix generator for DimToggle.
Generates structured release manifests (JSON and Markdown) and formats
GitHub Release descriptions with Minecraft-version-grouped download links,
file sizes, and SHA-256 checksums.
"""

import os
import sys
import glob
import json
import hashlib
import argparse

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
    # Expected format: dimtoggle-<mc>-<loader>-<version>.jar
    base = filename[:-4] if filename.endswith('.jar') else filename
    parts = base.split('-')
    if len(parts) >= 4 and parts[0] == 'dimtoggle':
        mc = parts[1]
        loader = parts[2]
        version = '-'.join(parts[3:])
        return mc, loader, version
    return None, None, None

def generate_from_github(tag_name, repo_name="KyroXova/DimToggle", token=None):
    import urllib.request
    url = f"https://api.github.com/repos/{repo_name}/releases/tags/{tag_name}"
    headers = {"User-Agent": "DimToggle-Release-Sync/2.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    manifest = []
    for asset in data.get("assets", []):
        filename = asset["name"]
        if filename.endswith("-dev.jar") or filename.endswith("-sources.jar") or not filename.endswith(".jar"):
            continue
        mc, loader, version = parse_jar_name(filename)
        size_bytes = asset["size"]
        download_url = asset["browser_download_url"]
        digest = asset.get("digest", "")
        sha256 = digest.replace("sha256:", "") if digest.startswith("sha256:") else "N/A"
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
    jars = sorted(glob.glob(os.path.join(jars_dir, '*.jar')))
    manifest = []
    
    for jar_path in jars:
        filename = os.path.basename(jar_path)
        if filename.endswith('-dev.jar') or filename.endswith('-sources.jar'):
            continue
        
        mc, loader, version = parse_jar_name(filename)
        size_bytes = os.path.getsize(jar_path)
        sha256 = compute_sha256(jar_path)
        download_url = f"https://github.com/{repo_name}/releases/download/{tag_name}/{filename}"
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

def generate_download_matrix_md(manifest, targets_json_path="targets.json"):
    by_mc = {}
    for entry in manifest:
        mc = entry["minecraft"]
        if mc not in by_mc:
            by_mc[mc] = {}
        by_mc[mc][entry["loader"]] = entry

    # Sort versions according to targets.json if available
    ordered_versions = []
    if os.path.exists(targets_json_path):
        with open(targets_json_path, 'r', encoding='utf-8') as f:
            targets_data = json.load(f)
            for t in targets_data.get('targets', []):
                ordered_versions.append(t['minecraft'])
    
    # Fallback to keys
    for mc in by_mc:
        if mc not in ordered_versions:
            ordered_versions.append(mc)

    lines = [
        "## Downloads & Artifact Matrix",
        "",
        "| Minecraft Version | Fabric | Forge | NeoForge |",
        "| :--- | :---: | :---: | :---: |"
    ]

    for mc in ordered_versions:
        if mc not in by_mc:
            continue
        row = by_mc[mc]
        
        # Fabric
        if "fabric" in row:
            f_entry = row["fabric"]
            f_cell = f"[{f_entry['size_formatted']}]({f_entry['download_url']})"
        else:
            f_cell = "N/A"
            
        # Forge
        if "forge" in row:
            fg_entry = row["forge"]
            fg_cell = f"[{fg_entry['size_formatted']}]({fg_entry['download_url']})"
        else:
            fg_cell = "N/A"
            
        # NeoForge
        if "neoforge" in row:
            nf_entry = row["neoforge"]
            nf_cell = f"[{nf_entry['size_formatted']}]({nf_entry['download_url']})"
        else:
            nf_cell = "N/A"
            
        lines.append(f"| **{mc}** | {f_cell} | {fg_cell} | {nf_cell} |")

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

def generate_manifest(jars_dir, tag_name, repo_name="KyroXova/DimToggle"):
    jars = sorted(glob.glob(os.path.join(jars_dir, '*.jar')))
    manifest = []
    
    for jar_path in jars:
        filename = os.path.basename(jar_path)
        if filename.endswith('-dev.jar') or filename.endswith('-sources.jar'):
            continue
        
        mc, loader, version = parse_jar_name(filename)
        size_bytes = os.path.getsize(jar_path)
        sha256 = compute_sha256(jar_path)
        download_url = f"https://github.com/{repo_name}/releases/download/{tag_name}/{filename}"
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

def main():
    parser = argparse.ArgumentParser(description="Generate release manifest and download matrix")
    parser.add_argument("--jars-dir", default="", help="Directory containing built JARs")
    parser.add_argument("--tag", required=True, help="Release tag name, e.g. v2.0.0")
    parser.add_argument("--repo", default="KyroXova/DimToggle", help="GitHub repo, e.g. KyroXova/DimToggle")
    parser.add_argument("--from-github", action="store_true", help="Fetch asset metadata directly from GitHub Release API")
    parser.add_argument("--changelog", default="", help="Path to base changelog markdown file")
    parser.add_argument("--out-manifest-json", default="release-manifest.json", help="Output JSON manifest file")
    parser.add_argument("--out-release-notes", default="release-notes.md", help="Output release notes markdown file")
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

if __name__ == '__main__':
    main()
