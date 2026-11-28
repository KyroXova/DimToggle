#!/usr/bin/env python3
"""
CurseForge release publisher and description sync for DimToggle.
Uploads release JARs with proper metadata (Minecraft version, ModLoader,
Client/Server environment, Java version) and syncs the project description.
"""

import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

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

def fetch_version_types(token):
    url = f"{CURSEFORGE_API_BASE}/game/version-types"
    if not url.startswith("https://"):
        raise ValueError(f"Insecure URL: {url}")
    headers = {
        "X-Api-Token": token,
        "User-Agent": "DimToggle-Release-Sync/2.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:  # nosec B310
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"Retrieved {len(data)} game version types from CurseForge.")
                return data
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        print(f"Notice: Failed to fetch CurseForge version types: {e}")
    return []

def fetch_game_versions(token):
    url = f"{CURSEFORGE_API_BASE}/game/versions"
    if not url.startswith("https://"):
        raise ValueError(f"Insecure URL: {url}")
    headers = {
        "X-Api-Token": token,
        "User-Agent": "DimToggle-Release-Sync/2.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:  # nosec B310
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"Retrieved {len(data)} game version identifiers from CurseForge.")
                return data
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Failed to fetch CurseForge game versions (HTTP {e.code}): {err}")
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        print(f"Exception fetching CurseForge game versions: {e}")
    return []

def fetch_existing_files(token, project_id):
    """
    Fetch existing files for the project to prevent duplicate uploads.
    Uses CurseForge's public files endpoints with pagination.
    """
    public_endpoints = [
        f"https://www.curseforge.com/api/v1/mods/{project_id}/files",
        f"https://api.curse.tools/v1/cf/mods/{project_id}/files"
    ]

    for base_url in public_endpoints:
        all_files = []
        index = 0
        page_size = 50
        success = False
        try:
            while True:
                url = f"{base_url}?pageSize={page_size}&index={index}"
                if not url.startswith("https://"):
                    raise ValueError(f"Insecure URL: {url}")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DimToggle-Release-Sync/2.0"
                }
                req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        items = data.get("data", [])
                        if not items:
                            success = True
                            break
                        all_files.extend(items)
                        total = data.get("pagination", {}).get("totalCount", len(all_files))
                        index += len(items)
                        if index >= total or len(items) < page_size:
                            success = True
                            break
                    else:
                        break
            if success and all_files:
                print(f"Retrieved {len(all_files)} existing file record(s) from CurseForge public API ({base_url.split('/')[2]}).")
                return all_files
        except (urllib.error.URLError, json.JSONDecodeError, OSError, TimeoutError) as exc:
            print(f"Notice: public endpoint {base_url} check failed: {exc}", file=sys.stderr)
            continue

    # Fallback: legacy upload API if token is present
    if token:
        url = f"{CURSEFORGE_API_BASE}/projects/{project_id}/files"
        if not url.startswith("https://"):
            raise ValueError(f"Insecure URL: {url}")
        headers = {
            "X-Api-Token": token,
            "User-Agent": "DimToggle-Release-Sync/2.0"
        }
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    print(f"Retrieved {len(data)} existing file record(s) from CurseForge upload API.")
                    return data
        except (urllib.error.URLError, json.JSONDecodeError, OSError, TimeoutError) as exc:
            print(f"Notice: legacy upload endpoint check skipped: {exc}", file=sys.stderr)

    return []

def build_version_indices(versions_list, version_types=None):
    """
    Build index lookups from CurseForge versions list,
    filtering out non-Java / Bedrock version types.
    """
    bad_type_ids = set()
    if version_types:
        for vt in version_types:
            vt_name = str(vt.get("name", "")).lower()
            vt_slug = str(vt.get("slug", "")).lower()
            if "bedrock" in vt_name or "bedrock" in vt_slug:
                bad_type_ids.add(vt.get("id"))

    name_map = {}
    slug_map = {}
    candidates_map = {}
    for item in versions_list:
        v_id = item.get("id")
        type_id = item.get("gameVersionTypeID")
        if type_id in bad_type_ids:
            continue

        name = str(item.get("name", "")).strip().lower()
        slug = str(item.get("slug", "")).strip().lower()
        if name and v_id:
            candidates_map.setdefault(name, []).append(v_id)
            if name not in name_map:
                name_map[name] = v_id
        if slug and v_id:
            candidates_map.setdefault(slug, []).append(v_id)
            if slug not in slug_map:
                slug_map[slug] = v_id
    return name_map, slug_map, candidates_map

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

    # 3. Environment: Server-side only
    for env in ["server"]:
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

    return sorted(matched_ids)

def sync_description(token, project_id, description_text):
    print(f"Updating CurseForge project description for Project ID: {project_id}...")
    url = f"{CURSEFORGE_API_BASE}/projects/{project_id}/description"
    headers = {
        "X-Api-Token": token,
        "Content-Type": "application/json",
        "User-Agent": "DimToggle-Release-Sync/2.0"
    }
    if not url.startswith("https://"):
        raise ValueError(f"Insecure URL: {url}")
    payload = json.dumps({"description": description_text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:  # nosec B310
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
    except (urllib.error.URLError, OSError) as e:
        print(f"Failed to update CurseForge description: {e}")
        return False

def upload_file_multipart(token, project_id, jar_path, metadata_dict, candidates_map=None):
    url = f"{CURSEFORGE_API_BASE}/projects/{project_id}/upload-file"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    
    filename = os.path.basename(jar_path)
    metadata_json = json.dumps(metadata_dict)

    with open(jar_path, "rb") as f:
        file_bytes = f.read()

    body = bytearray()
    
    # Metadata field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="metadata"\r\n\r\n')
    body.extend(metadata_json.encode("utf-8"))
    body.extend(b"\r\n")

    # File field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.extend(b"Content-Type: application/java-archive\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode())

    headers = {
        "X-Api-Token": token,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
        "User-Agent": "DimToggle-Release-Sync/2.0"
    }

    if not url.startswith("https://"):
        raise ValueError(f"Insecure URL: {url}")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:  # nosec B310
            res_data = resp.read().decode("utf-8")
            print(f"Uploaded {filename} -> CurseForge response: {res_data}")
            return True
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Failed to upload {filename} (HTTP {e.code}): {err}")
        # If already exists or duplicate, don't fail entire run
        if "already exists" in err.lower() or "duplicate" in err.lower():
            return True
        import re
        m = re.search(r"Invalid game version ID:\s*(\d+)", err)
        if m:
            bad_id = int(m.group(1))
            gvs = metadata_dict.get("gameVersions", [])
            if bad_id in gvs:
                replacement = None
                if candidates_map:
                    for cand_list in candidates_map.values():
                        if bad_id in cand_list:
                            for c in cand_list:
                                if c != bad_id and c not in gvs:
                                    replacement = c
                                    break
                        if replacement:
                            break
                if replacement:
                    print(f"Replacing invalid version ID {bad_id} with candidate {replacement} for {filename}...")
                    metadata_dict["gameVersions"] = [replacement if x == bad_id else x for x in gvs]
                else:
                    print(f"Retrying {filename} without invalid version ID {bad_id}...")
                    metadata_dict["gameVersions"] = [x for x in gvs if x != bad_id]
                return upload_file_multipart(token, project_id, jar_path, metadata_dict, candidates_map)
        return False
    except (urllib.error.URLError, OSError) as e:
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

    # 1. Update Project Description
    desc_path = "Curseforge-desc.md" if os.path.exists("Curseforge-desc.md") else "README.md"
    if os.path.exists(desc_path):
        with open(desc_path, "r", encoding="utf-8") as f:
            description = f.read()
        sync_description(token, project_id, description)

    # 2. Query Game Versions for tag matching
    cf_version_types = fetch_version_types(token)
    cf_versions = fetch_game_versions(token)
    name_map, slug_map, candidates_map = build_version_indices(cf_versions, cf_version_types)

    # 3. Query Existing Files for duplicate prevention
    existing_files = fetch_existing_files(token, project_id)
    existing_filenames = set()
    existing_display_names = set()
    for f in existing_files:
        if isinstance(f, dict):
            fn = str(f.get("fileName", "")).strip().lower()
            dn = str(f.get("displayName", "")).strip().lower()
            if fn:
                existing_filenames.add(fn)
            if dn:
                existing_display_names.add(dn)
    if existing_filenames or existing_display_names:
        print(f"Indexed {len(existing_filenames)} unique existing file names and {len(existing_display_names)} display names on CurseForge.")

    # 4. Discover and upload all built JARs
    jar_patterns = [
        "release-jars/*.jar",
        "build/*/*/libs/*.jar"
    ]
    jars = []
    for pattern in jar_patterns:
        jars.extend(glob.glob(pattern))

    jars = sorted(set(jars))
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

        # Check for duplicates on CurseForge
        if filename.lower() in existing_filenames or display_name.lower() in existing_display_names:
            print(f"Skipping {filename}: already exists on CurseForge ({display_name}).")
            success_count += 1
            continue
        # Load changelog from changelogs/ directory if present
        changelog_path = os.path.join("changelogs", f"changelog_1.0.0_to_{file_version}.md")
        if not os.path.exists(changelog_path):
            changelog_path = os.path.join("changelogs", f"changelog_{file_version}.md")
        if os.path.exists(changelog_path):
            with open(changelog_path, "r", encoding="utf-8") as cf:
                changelog = cf.read()
        else:
            changelog = (
                f"### DimToggle {file_version} for Minecraft {mc} ({loader.capitalize()})\n\n"
                f"- Server-side dimension access and locking utility.\n"
                f"- Environment: Server-side (clients do not need to install).\n"
                f"- Full release notes: https://github.com/KyroXova/DimToggle/releases/tag/v{file_version}"
            )

        release_type = os.environ.get("CURSEFORGE_RELEASE_TYPE", "release")
        metadata = {
            "changelog": changelog,
            "changelogType": "markdown",
            "displayName": display_name,
            "gameVersions": version_ids,
            "releaseType": release_type
        }

        print(f"Uploading {display_name} (Versions: {version_ids})...")
        ok = upload_file_multipart(token, project_id, jar_path, metadata, candidates_map)
        if ok:
            success_count += 1
        else:
            fail_count += 1
        # Moderate upload rate
        time.sleep(1)

    print(f"CurseForge upload complete: {success_count} succeeded, {fail_count} failed.")
    if fail_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
