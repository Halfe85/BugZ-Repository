#!/usr/bin/env python3
"""Check both BugZ distribution catalogs and locally published archives.

This is an artifact consistency check, NOT a Kodi/Jellyfin runtime test.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW_PREFIX = "https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/"
problems: list[str] = []


def check(condition: bool, explanation: str) -> None:
    if not condition:
        problems.append(explanation)


def archive(path: Path, required_member: str | None = None) -> None:
    check(path.is_file(), f"Missing ZIP: {path.relative_to(ROOT)}")
    if not path.is_file():
        return
    if not zipfile.is_zipfile(path):
        problems.append(f"Invalid ZIP: {path.relative_to(ROOT)}")
        return
    with zipfile.ZipFile(path) as file:
        check(file.testzip() is None, f"Corrupt ZIP member: {path.relative_to(ROOT)}")
        names = file.namelist()
        if required_member:
            check(required_member in names, f"Missing {required_member} in {path.relative_to(ROOT)}")


def md5_check(path: Path, digest: str) -> None:
    if path.is_file():
        actual = hashlib.md5(path.read_bytes()).hexdigest()
        check(actual.lower() == digest.strip().lower(), f"MD5 mismatch for {path.relative_to(ROOT)}")


def main() -> int:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    check(isinstance(manifest, list) and bool(manifest), "Jellyfin manifest must contain plugins")
    if isinstance(manifest, list):
        for plugin in manifest:
            name = plugin.get("name", "(unknown)")
            try:
                uuid.UUID(plugin["guid"])
            except (ValueError, KeyError, TypeError):
                problems.append(f"Invalid GUID for Jellyfin plugin {name}")
            versions = plugin.get("versions", [])
            check(bool(versions), f"No Jellyfin releases for {name}")
            for version in versions:
                url = version.get("sourceUrl", "")
                check(url.startswith(RAW_PREFIX + "packages/"), f"Unexpected Jellyfin package URL: {url}")
                if not url.startswith(RAW_PREFIX + "packages/"):
                    continue
                relative = unquote(urlparse(url).path.split("/main/", 1)[-1])
                file = ROOT / relative
                check(file.is_relative_to(ROOT / "packages"), f"Package outside packages/: {relative}")
                if not file.is_relative_to(ROOT / "packages"):
                    continue
                archive(file)
                if file.is_file() and zipfile.is_zipfile(file):
                    with zipfile.ZipFile(file) as jar:
                        check(any(item.lower().endswith(".dll") for item in jar.namelist()),
                              f"No .NET assembly in {relative}")
                md5_check(file, version.get("checksum", ""))
                check(bool(version.get("targetAbi")), f"Missing Jellyfin ABI: {relative}")

    for catalog in ("addons.xml", "dependencies.xml"):
        file = ROOT / "kodi" / catalog
        ET.parse(file)
        md5_check(file, (file.parent / (catalog + ".md5")).read_text(encoding="utf-8"))
    addons = ET.parse(ROOT / "kodi/addons.xml").getroot()
    check(addons.tag == "addons", "Kodi main catalog is not <addons>")
    for addon in addons.findall("addon"):
        addon_id, version = addon.get("id"), addon.get("version")
        if not addon_id or not version:
            problems.append("Kodi entry missing addon ID or version")
            continue
        archive(ROOT / "kodi" / addon_id / f"{addon_id}-{version}.zip",
                required_member=f"{addon_id}/addon.xml")

    # Pages must expose a root-level installer so Kodi can discover it directly.
    latest = ROOT / "kodi/repository.bugz/repository.bugz-1.0.0.zip"
    root_installer = ROOT / "repository.bugz-1.0.0.zip"
    archive(root_installer, required_member="repository.bugz/addon.xml")
    if latest.is_file() and root_installer.is_file():
        check(latest.read_bytes() == root_installer.read_bytes(), "Root Kodi installer differs from published ZIP")

    if problems:
        for problem in problems:
            print("FAIL:", problem, file=sys.stderr)
        return 1
    print(f"PASS: {len(manifest)} Jellyfin plugin(s), "
          f"{len(addons.findall('addon'))} Kodi catalog entry/entries, "
          "catalog checksums and local ZIPs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
