#!/usr/bin/env python3
"""
CurseForge release publisher and description sync for DimToggle.
Uploads release JARs with proper metadata (Minecraft version, ModLoader,
Client/Server environment, Java version) and syncs the project description.
"""

import os
import sys
import json
import glob
import uuid
import time
import urllib.request
import urllib.error

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

def load_target_properties(mc):
    props = {}
    path = f"properties/{mc}.properties"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    props[k.strip()] = v.strip()
    return props

def fetch_game_versions(token):
    url = f"{CURSEFORGE_API_BASE}/game/versions"
    headers = {
        "X-Api-Token": token,
        "User-Agent": "DimToggle-Release-Sync/2.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"Retrieved {len(data)} game version identifiers from CurseForge.")
                return data
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Failed to fetch CurseForge game versions (HTTP {e.code}): {err}")
    except Exception as e:
        print(f"Exception fetching CurseForge game versions: {e}")
    return []

def build_version_indices(versions_list):
    """
    Build index lookups from CurseForge versions list.
    """
    name_map = {}
    slug_map = {}
    for item in versions_list:
        v_id = item.get("id")
        name = str(item.get("name", "")).strip().lower()
        slug = str(item.get("slug", "")).strip().lower()
        if name and v_id:
            name_map[name] = v_id
        if slug and v_id:
            slug_map[slug] = v_id
    return name_map, slug_map

def resolve_game_version_ids(mc, loader, java_release, name_map, slug_map):
    """
    Resolve CurseForge integer IDs for:
    - Minecraft version
    - Loader (Fabric / Forge / NeoForge)
    - Environment (Both Client and Server)
    - Java version
    """
    matched_ids = set()

    # 1. Minecraft version
    mc_lower = mc.lower()
    mc_slug = mc.replace(".", "-").lower()
    if mc_lower in name_map:
        matched_ids.add(name_map[mc_lower])
    elif f"minecraft {mc_lower}" in name_map:
        matched_ids.add(name_map[f"minecraft {mc_lower}"])
    elif mc_slug in slug_map:
        matched_ids.add(slug_map[mc_slug])
    else:
        print(f"Warning: Could not resolve CurseForge version ID for Minecraft {mc}")

    # 2. Loader
    loader_lower = loader.lower()
    if loader_lower in name_map:
        matched_ids.add(name_map[loader_lower])
    elif loader_lower in slug_map:
        matched_ids.add(slug_map[loader_lower])
    else:
        print(f"Warning: Could not resolve CurseForge version ID for loader {loader}")

    # 3. Environment: Both Client and Server
    for env in ["client", "server"]:
        if env in name_map:
            matched_ids.add(name_map[env])
        elif env in slug_map:
            matched_ids.add(slug_map[env])

    # 4. Java version
    if java_release:
        java_str = f"java {java_release}"
        java_slug = f"java-{java_release}"
        if java_str in name_map:
            matched_ids.add(name_map[java_str])
        elif java_slug in slug_map:
            matched_ids.add(slug_map[java_slug])

    return sorted(list(matched_ids))

def sync_description(token, project_id, description_text):
    print(f"Updating CurseForge project description for Project ID: {project_id}...")
    url = f"{CURSEFORGE_API_BASE}/projects/{project_id}/description"
    headers = {
        "X-Api-Token": token,
        "Content-Type": "application/json",
        "User-Agent": "DimToggle-Release-Sync/2.0"
    }
    payload = json.dumps({"description": description_text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 204):
                print("CurseForge project description updated successfully.")
                return True
            else:
                print(f"CurseForge description update returned HTTP status {resp.status}")
                return False
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"CurseForge description update HTTP {e.code}: {e.reason}\n{err}")
        return False
    except Exception as e:
        print(f"Failed to update CurseForge description: {e}")
        return False

def upload_file_multipart(token, project_id, jar_path, metadata_dict):
    url = f"{CURSEFORGE_API_BASE}/projects/{project_id}/upload-file"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    
    filename = os.path.basename(jar_path)
    metadata_json = json.dumps(metadata_dict)

    with open(jar_path, "rb") as f:
        file_bytes = f.read()

    body = bytearray()
    
    # Metadata field
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="metadata"\r\n\r\n')
    body.extend(metadata_json.encode("utf-8"))
    body.extend(b"\r\n")

    # File field
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: application/java-archive\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    headers = {
        "X-Api-Token": token,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
        "User-Agent": "DimToggle-Release-Sync/2.0"
    }

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = resp.read().decode("utf-8")
            print(f"Uploaded {filename} -> CurseForge response: {res_data}")
            return True
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Failed to upload {filename} (HTTP {e.code}): {err}")
        # If already exists or duplicate, don't fail entire run
        if "already exists" in err.lower() or "duplicate" in err.lower():
            return True
        return False
    except Exception as e:
        print(f"Error uploading {filename}: {e}")
        return False

def main():
    token = os.environ.get("CURSEFORGE_TOKEN") or os.environ.get("CURSEFORGE_API_KEY")
    project_id = os.environ.get("CURSEFORGE_PROJECT_ID")

    props = load_mod_properties()
    if not project_id:
        project_id = props.get("curseforge.project.id")

    mod_version = props.get("mod.version", "2.0.0")

    if not token:
        print("Notice: CURSEFORGE_TOKEN is not configured. Skipping CurseForge sync/upload.")
        sys.exit(0)

    if not project_id:
        print("Notice: CurseForge Project ID not found. Set CURSEFORGE_PROJECT_ID secret or curseforge.project.id in properties/mod.properties.")
        sys.exit(0)

    print(f"Starting CurseForge release sync for DimToggle {mod_version} (Project ID: {project_id})...")

    # 1. Update Project Description from README
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            description = f.read()
        sync_description(token, project_id, description)

    # 2. Query Game Versions for tag matching
    cf_versions = fetch_game_versions(token)
    name_map, slug_map = build_version_indices(cf_versions)

    # 3. Discover and upload all built JARs
    jar_patterns = [
        "release-jars/*.jar",
        "build/*/*/libs/*.jar"
    ]
    jars = []
    for pattern in jar_patterns:
        jars.extend(glob.glob(pattern))

    jars = sorted(list(set(jars)))
    # Exclude source/dev jars
    release_jars = [j for j in jars if not j.endswith("-dev.jar") and not j.endswith("-sources.jar")]

    if not release_jars:
        print("No release JARs found to upload to CurseForge.")
        sys.exit(0)

    print(f"Found {len(release_jars)} release JAR(s) to process for CurseForge upload.")

    success_count = 0
    fail_count = 0

    for jar_path in release_jars:
        filename = os.path.basename(jar_path)
        # Parse dimtoggle-{mc}-{loader}-{version}.jar
        name_no_ext = os.path.splitext(filename)[0]
        parts = name_no_ext.split("-")
        if len(parts) >= 4 and parts[0] == "dimtoggle":
            mc = parts[1]
            loader = parts[2]
            file_version = "-".join(parts[3:])
        else:
            print(f"Skipping non-standard jar name: {filename}")
            continue

        target_props = load_target_properties(mc)
        java_release = target_props.get("java.release")

        version_ids = resolve_game_version_ids(mc, loader, java_release, name_map, slug_map)

        display_name = f"DimToggle {file_version} [{mc}] [{loader.capitalize()}]"
        changelog = (
            f"### DimToggle {file_version} for Minecraft {mc} ({loader.capitalize()})\n\n"
            f"- Multi-loader support across Fabric, Forge, and NeoForge.\n"
            f"- Environment: Client & Server compatible.\n"
            f"- Full release notes: https://github.com/KyroXova/DimToggle/releases/tag/v{file_version}"
        )

        metadata = {
            "changelog": changelog,
            "changelogType": "markdown",
            "displayName": display_name,
            "parentFileID": None,
            "gameVersions": version_ids,
            "releaseType": "release"
        }

        print(f"Uploading {display_name} (Versions: {version_ids})...")
        ok = upload_file_multipart(token, project_id, jar_path, metadata)
        if ok:
            success_count += 1
        else:
            fail_count += 1
        # Moderate upload rate
        time.sleep(1)

    print(f"CurseForge upload complete: {success_count} succeeded, {fail_count} failed.")

if __name__ == "__main__":
    main()
