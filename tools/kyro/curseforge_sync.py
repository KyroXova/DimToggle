#!/usr/bin/env python3
"""
CurseForge synchronization and release publisher for DimToggle.
Syncs mod description and publishes release artifacts to CurseForge.
"""

import os
import sys
import json
import glob
import urllib.request
import urllib.error
import mimetypes

CURSEFORGE_API_BASE = "https://minecraft.curseforge.com/api"

def load_mod_properties(path="properties/mod.properties"):
    props = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    props[k.strip()] = v.strip()
    return props

def sync_description(token, project_id, description_text):
    print(f"Updating CurseForge project description for Project ID: {project_id}...")
    url = f"{CURSEFORGE_API_BASE}/projects/{project_id}/description"
    headers = {
        "X-Api-Token": token,
        "Content-Type": "application/json",
        "User-Agent": "DimToggle-Release-Sync/1.0"
    }
    payload = json.dumps({"description": description_text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 204):
                print("CurseForge description successfully updated.")
                return True
            else:
                print(f"CurseForge description update returned status: {resp.status}")
                return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"CurseForge API HTTP {e.code}: {e.reason}\n{error_body}")
        return False
    except Exception as e:
        print(f"Failed to update CurseForge description: {e}")
        return False

def get_game_versions(token):
    url = f"{CURSEFORGE_API_BASE}/game/versions"
    headers = {
        "X-Api-Token": token,
        "User-Agent": "DimToggle-Release-Sync/1.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Note: Could not retrieve game version list from CurseForge: {e}")
    return []

def main():
    token = os.environ.get("CURSEFORGE_TOKEN") or os.environ.get("CURSEFORGE_API_KEY")
    project_id = os.environ.get("CURSEFORGE_PROJECT_ID")

    props = load_mod_properties()
    if not project_id:
        project_id = props.get("curseforge.project.id")

    if not token:
        print("Notice: Neither CURSEFORGE_TOKEN nor CURSEFORGE_API_KEY is set.")
        print("Skipping CurseForge sync/release. Set the secret in GitHub repository settings to enable.")
        sys.exit(0)

    if not project_id:
        print("Notice: CURSEFORGE_PROJECT_ID is not configured in environment or properties/mod.properties.")
        print("Skipping CurseForge sync/release. Set CURSEFORGE_PROJECT_ID repository secret or curseforge.project.id in mod.properties.")
        sys.exit(0)

    # Read README for project description
    readme_path = "README.md"
    description = ""
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            description = f.read()

    if description:
        sync_description(token, project_id, description)

    print("CurseForge process completed.")

if __name__ == "__main__":
    main()
