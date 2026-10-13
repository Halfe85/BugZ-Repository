# Jellyfin plugin repository

BugZ's Jellyfin catalog is already published at:

```text
https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/manifest.json
```

## Install JellyTaku

1. Open Jellyfin **Dashboard → Plugins → Repositories / Manage Repositories**.
2. Add a repository named **BugZ** and paste the URL above.
3. Go to **Plugins → Catalog** and install **JellyTaku**, if a version compatible with your Jellyfin server appears.
4. Restart the Jellyfin server and follow the plugin's configuration instructions.

As of October 13, 2026, this catalog lists JellyTaku **0.0.6.0** (and prior releases). Its current target ABI is **12.0.0.0** (Jellyfin 12). Jellyfin filters plugin versions based on server compatibility.

The JellyTaku package is **not a Kodi addon**. Its archive contains a .NET assembly (`Jellytaku.Plugin.Jellyfin.dll`) and a Python backend plus administration assets. Make sure Python 3 is installed where Jellyfin runs; container-based installations must provide it inside the container. The manifest does not install Python automatically.

## Publishing new Jellyfin releases

The existing stable manifest location and ZIP paths are intentionally preserved. When publishing a new JellyTaku release:

1. Publish its versioned ZIP into `packages/` (retain previously published versions).
2. Update `manifest.json` by prepending a new compatible version entry under JellyTaku. Keep the same plugin GUID.
3. Set `version`, `targetAbi`, `sourceUrl`, `timestamp`, and `checksum` correctly. Jellyfin's `checksum` is the **MD5 of the exact ZIP bytes**, not the Git blob SHA or SHA-256.
4. Run `python3 tools/verify_repositories.py` before merging/publishing.
5. Verify installation, startup, backend availability, and updates on an actual Jellyfin server. Metadata verification is not a runtime test.

Do **not** put Kodi's `addons.xml` in Jellyfin's repository settings; Jellyfin expects the JSON manifest.

The repo's Kodi installation entry point is described in [KODI.md](KODI.md).

## Current development stage

Pre-alpha `v0.0.6` is shown to Jellyfin as numeric `0.0.6.0`. Historical
packages have been renamed from `0.1.x` to `0.0.x` without rebuilding archives.
