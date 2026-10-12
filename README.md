# BugZ Repository

Public distribution catalogs for Jellyfin plugins and Kodi addons.

This repository contains release artifacts and packaging utilities: the Jellyfin
`manifest.json` and plugin ZIPs under `packages/`, plus Kodi packages and catalog
files under `kodi/`.
Plugin source code and build workflows remain in their respective private
source repositories.

## Kodi: modified Otaku

Download and install [BugZ Kodi Repository](https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/kodi/repository.bugz/repository.bugz-1.0.0.zip) using Kodi's **Install from zip file**.
Then open **Install from repository → BugZ Kodi Repository → Video add-ons → Otaku**.
Restart Kodi after updating and keep AnimePahe enabled in Otaku's provider settings.

The custom Otaku version is `5.3.3+bugz.1`; its addon ID remains `plugin.video.otaku`
so it uses the existing Otaku settings. AnimePahe keeps its name while using
Megaplay internally, with AniList/MAL lookup, source decoding, fresh playback
CDN tokens, Kodi subtitle preferences, and diagnostic logging. The repository
also indexes the required `context.otaku` 1.0.35 dependency from its upstream Hooty distribution. Other dependencies
come from Kodi's official repository or already configured addon repositories.
Kodi 20 or later is required by the packaged Otaku dependency declaration.

[Direct modified Otaku ZIP](https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/kodi/plugin.video.otaku/plugin.video.otaku-5.3.3%2Bbugz.1.zip)

Download the repository ZIP to storage accessible to Kodi, including a USB drive,
Shield Downloads, or an existing network share. GitHub's repository page itself
is not a Kodi file-manager download source. The repository addon uses permanent
GitHub HTTPS catalog/package URLs once installed; no local HTTP server is needed.

Detailed installation, logging, and rebuild instructions: [KODI.md](KODI.md).

## Jellyfin catalog URL

```text
https://raw.githubusercontent.com/Halfe85/BugZ-Repository/main/manifest.json
```

In Jellyfin, open **Dashboard → Plugins → Repositories** and add this URL.
Published releases will appear under **Plugins → Catalog** when compatible
with your Jellyfin server version.

## JellyTaku

JellyTaku is being developed for Jellyfin 12 with a C# plugin, an automatically
started Python service, and an Angular management dashboard.

**No JellyTaku release has been published yet.** The catalog starts as an
empty JSON array, and the source-side release workflow will add an entry and
ZIP once enabled and approved. Python 3 must be available on the Jellyfin host
(or in its container); releases bundle Python modules but not the interpreter.

Do not commit source credentials, watchlists, tokens, personal data, or
backend SQLite databases to this public repository.
