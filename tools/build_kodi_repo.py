#!/usr/bin/env python3
"""Package a local Otaku snapshot and generate BugZ's Kodi distribution catalog."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/kodi/'
REPO_ID = 'repository.bugz'
CONTEXT_URL = 'https://raw.githubusercontent.com/Goldenfreddy0703/repository.hooty/master/repo/zips/'


def addon_files(path):
    for item in sorted(path.rglob('*')):
        rel = item.relative_to(path)
        if any(part.startswith('.') or part == '__pycache__' for part in rel.parts):
            continue
        if not item.is_file() or item.suffix.lower() in ('.pyc', '.pyo', '.db', '.log', '.bak', '.tmp'):
            continue
        if item.is_symlink():
            raise ValueError('Symlink in addon: ' + str(item))
        yield item, rel


def capture(source, destination):
    if destination.exists():
        raise ValueError('Snapshot already exists: ' + str(destination))
    for path, rel in addon_files(source):
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def zip_addon(source, manifest, extra=None, output_root=None):
    addon_id, version = manifest.get('id'), manifest.get('version')
    out = (output_root or ROOT / 'kodi') / addon_id
    out.mkdir(parents=True, exist_ok=True)
    archive = out / (addon_id + '-' + version + '.zip')
    contents = {rel.as_posix(): path.read_bytes() for path, rel in addon_files(source)}
    contents['addon.xml'] = ET.tostring(manifest, encoding='utf-8', xml_declaration=True)
    contents.update(extra or {})
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        # Explicit directories also make the top-level addon folder unambiguous.
        directories = {addon_id + '/'}
        for name in contents:
            directories.update(str(parent) + '/' for parent in (Path(addon_id) / name).parents
                               if str(parent) != '.')
        for name in sorted(directories):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 12, 0, 0, 0))
            info.external_attr = (0o40755 << 16) | 0x10
            package.writestr(info, b'')
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(addon_id + '/' + name, date_time=(2026, 10, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            package.writestr(info, data)
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert ET.fromstring(package.read(addon_id + '/addon.xml')).get('version') == version
        for name, data in contents.items():
            assert package.read(addon_id + '/' + name) == data
            if name.endswith('.py'):
                ast.parse(data, filename=name, feature_version=(3, 8))
    for node in manifest.findall('extension/assets/*'):
        if not node.text:
            continue
        rel = Path(node.text)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Invalid asset path')
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents[rel.as_posix()])
    if 'changelog.txt' in contents:
        (out / ('changelog-' + version + '.txt')).write_bytes(contents['changelog.txt'])
    (out / 'addon.xml').write_bytes(contents['addon.xml'])
    (Path(str(archive) + '.sha256')).write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + '\n')
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-installed', type=Path)
    parser.add_argument('--otaku-version', default='5.3.3+bugz.2')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9.+_~]+', args.otaku_version):
        parser.error('Invalid Kodi version')
    snapshots = ROOT / '_local' / 'source'
    if args.capture_installed:
        for addon_id in ('plugin.video.otaku', 'context.otaku'):
            capture(args.capture_installed / addon_id, snapshots / addon_id)
    otaku_source, context_source = snapshots / 'plugin.video.otaku', snapshots / 'context.otaku'
    if not otaku_source.exists() or not context_source.exists():
        parser.error('Capture local addons first with --capture-installed PATH_TO_KODI_ADDONS')
    if args.otaku_version == '5.3.3+bugz.2':
        resolver = (otaku_source / 'resources/lib/windows/resolver.py').read_text()
        if 'STARTUP_DELAY_SECONDS = 3.0' not in resolver:
            parser.error('This release requires the startup-delay source. Extract the published bugz.2 ZIP into _local/source/ or capture an installed bugz.2 addon.')
    repository_source = ROOT / 'repository.bugz'
    repository_source.mkdir(exist_ok=True)
    repo = ET.Element('addon', {'id': REPO_ID, 'name': 'BugZ Kodi Repository', 'version': '1.0.0', 'provider-name': 'Halfe85'})
    requires = ET.SubElement(repo, 'requires')
    ET.SubElement(requires, 'import', {'addon': 'xbmc.addon', 'version': '12.0.0'})
    extension = ET.SubElement(repo, 'extension', {'point': 'xbmc.addon.repository', 'name': 'BugZ Kodi Repository'})
    directory = ET.SubElement(extension, 'dir', {'minversion': '20.0.0'})
    ET.SubElement(directory, 'info', {'compressed': 'false'}).text = BASE_URL + 'addons.xml'
    ET.SubElement(directory, 'checksum').text = BASE_URL + 'addons.xml.md5'
    ET.SubElement(directory, 'datadir', {'zip': 'true'}).text = BASE_URL
    ET.SubElement(directory, 'hashes').text = 'false'
    dependency_dir = ET.SubElement(extension, 'dir', {'minversion': '20.0.0'})
    ET.SubElement(dependency_dir, 'info', {'compressed': 'false'}).text = BASE_URL + 'dependencies.xml'
    ET.SubElement(dependency_dir, 'checksum').text = BASE_URL + 'dependencies.xml.md5'
    ET.SubElement(dependency_dir, 'datadir', {'zip': 'true'}).text = CONTEXT_URL
    ET.SubElement(dependency_dir, 'hashes').text = 'false'
    metadata = ET.SubElement(repo, 'extension', {'point': 'xbmc.addon.metadata'})
    ET.SubElement(metadata, 'summary', {'lang': 'en_GB'}).text = 'BugZ repository for Kodi addons'
    ET.SubElement(metadata, 'description', {'lang': 'en_GB'}).text = 'Modified Otaku with Megaplay inside AnimePahe, and its required Otaku context menu addon.'
    ET.SubElement(metadata, 'platform').text = 'all'
    (repository_source / 'addon.xml').write_bytes(ET.tostring(repo, encoding='utf-8', xml_declaration=True))
    otaku = ET.parse(otaku_source / 'addon.xml').getroot()
    original_version = otaku.get('version')
    otaku.set('version', args.otaku_version)
    changes = ('BugZ custom build based on installed Otaku ' + original_version + '.\n'
               'AnimePahe retains its identity and uses Megaplay internally.\n'
               'AniList/MAL lookup, AES source decoding, fresh playback CDN tokens,\n'
               'Kodi subtitle preferences and diagnostic file logging are included.\n'
               'Loaded video is held paused for 3 seconds before playback begins.\n'
               'Original authors: TeamOtaku. Original addon license: GPL-3.0.\n'
               'This is a custom distribution, not an upstream TeamOtaku release.\n')
    changelog = changes.encode() + b'\n' + (otaku_source / 'changelog.txt').read_bytes()
    context = ET.parse(context_source / 'addon.xml').getroot()
    archives = [zip_addon(otaku_source, otaku, {'BUGZ-CHANGES.txt': changes.encode(), 'changelog.txt': changelog}),
                zip_addon(repository_source, repo)]
    # Publish a root-level Kodi installer for GitHub Pages File manager sources.
    # Keep kodi/repository.bugz/ as the unchanged auto-update download location.
    shutil.copyfile(archives[1], ROOT / archives[1].name)
    catalog = ET.Element('addons')
    for manifest in (repo, otaku):
        catalog.append(manifest)
    catalog_data = ET.tostring(catalog, encoding='utf-8', xml_declaration=True)
    (ROOT / 'kodi' / 'addons.xml').write_bytes(catalog_data)
    (ROOT / 'kodi' / 'addons.xml.md5').write_text(hashlib.md5(catalog_data).hexdigest() + '\n')
    dependency_catalog = ET.Element('addons')
    dependency_catalog.append(context)
    dependency_data = ET.tostring(dependency_catalog, encoding='utf-8', xml_declaration=True)
    (ROOT / 'kodi' / 'dependencies.xml').write_bytes(dependency_data)
    (ROOT / 'kodi' / 'dependencies.xml.md5').write_text(hashlib.md5(dependency_data).hexdigest() + '\n')
    zip_addon(context_source, context, output_root=ROOT / '_local' / 'dependencies')
    checksum_lines = [hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.relative_to(ROOT).as_posix() for archive in archives]
    (ROOT / 'kodi' / 'SHA256SUMS').write_text('\n'.join(checksum_lines) + '\n')
    report = {'source_version': original_version, 'package_version': args.otaku_version,
              'addon_id': 'plugin.video.otaku', 'snapshots': str(snapshots),
              'packages': [p.relative_to(ROOT).as_posix() for p in archives],
              'crc_and_python38_syntax': 'passed', 'installed_kodi_modified': False,
              'shield_install_or_playback_tested': False}
    (ROOT / '_local' / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
