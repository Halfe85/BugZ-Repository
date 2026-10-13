# BugZ Repository

**One GitHub repository, two native plugin distribution systems:** Kodi addons and Jellyfin server plugins.

The project publishes release artifacts and catalogs. Kodi and Jellyfin **do not share an executable addon format**: Kodi installs Python addons from XML/ZIP, while Jellyfin installs its own compiled server plugins from a JSON manifest and plugin ZIPs.

## Quick installation

| Platform | Published addon/plugin | Install repository |
| --- | --- | --- |
| Kodi 20+ | Modified Otaku `5.3.3+bugz.1` | [Kodi repository installer](https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/repository.bugz-1.0.0.zip) |
| Jellyfin 12 (ABI 12.0.0.0) | JellyTaku `0.0.6.0` | [Jellyfin manifest](https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/manifest.json) |

### Kodi

1. Download the [repository installer ZIP](https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/repository.bugz-1.0.0.zip), and save it to local/shared storage Kodi can read. GitHub Pages does not provide Kodi-compatible automatic directory listings; do not depend on browsing it as a Kodi File manager source.
2. Add-ons → Install from zip file → navigate to the downloaded `repository.bugz-1.0.0.zip`.
3. Install from repository → BugZ Kodi Repository → Video add-ons → Otaku.

The modified Otaku addon retains the ID `plugin.video.otaku` and its existing settings. Its AnimePahe provider uses Megaplay internally. The catalog also includes the `context.otaku` dependency from the upstream Hooty repository. Other dependencies are supplied by Kodi or other configured addon repositories. For version pinning, logging, and rebuilding, see [KODI.md](KODI.md).

### Jellyfin

1. On your Jellyfin server, open **Dashboard → Plugins → Repositories**.
2. Add a repository named `BugZ` using this **exact JSON manifest URL**:

   ```text
   https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/manifest.json
   ```
3. Under **Plugins → Catalog**, install **JellyTaku** if your server version is compatible.
4. Restart Jellyfin.

JellyTaku version `0.0.6.0` is currently published and declares target ABI `12.0.0.0`. The plugin packages contain a C# assembly and a Python backend with an administration UI; a working Python 3 installation is required on the Jellyfin host/container. See [JELLYFIN.md](JELLYFIN.md).

## Distribution layout

```text
index.html                           GitHub Pages landing page for both platforms
repository.bugz-1.0.0.zip            Kodi installer ZIP discoverable at website root
manifest.json                        Jellyfin plugin catalog (stable URL)
packages/                            Jellyfin plugin release ZIPs
kodi/addons.xml                      Kodi addon catalog
kodi/addons.xml.md5                  Kodi catalog checksum
kodi/dependencies.xml                Kodi external dependency catalog
kodi/dependencies.xml.md5            External catalog checksum
kodi/repository.bugz/                Kodi repository installer and addon metadata
kodi/plugin.video.otaku/             Modified Kodi Otaku ZIP and metadata
repository.bugz/addon.xml            Kodi repository source manifest
tools/build_kodi_repo.py             Local Kodi release packager
tools/verify_repositories.py         Checks both distribution catalogs and archives
```

**Compatibility commitment:** Existing Kodi update URLs under `kodi/` and the existing Jellyfin URL `manifest.json` remain unchanged. The website provides a single installation entry point; the plugin engines remain separate.

To validate both distributions locally, run `python3 tools/verify_repositories.py`. GitHub Actions also runs this verification on changes.

GitHub Pages is optional for normal catalog updates, but must be enabled (Settings → Pages → Deploy from branch → `main` → `/(root)`) for installation through Kodi's HTTP File manager source.

Plugin source code and release workflows may be maintained in separate source repositories. Never commit login credentials, tokens, user databases, watchlists, or service configuration secrets here.

## Pre-alpha version labels

The current JellyTaku release is pre-alpha `v0.0.6` (Jellyfin manifest: `0.0.6.0`).
Previous `0.1.x` packages are now relabeled `0.0.x` with the original archive bytes
and MD5 checksums retained. Alpha (`vX.aY.Z`) and beta (`vX.bY.Z`) have not begun.
