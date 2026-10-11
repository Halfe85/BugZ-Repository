# BugZ Jellyfin Plugin Repository

Public distribution catalog for Jellyfin plugins.

This repository contains **release artifacts only**: the Jellyfin plugin
`manifest.json` and versioned plugin ZIPs under `packages/`.
Plugin source code and build workflows remain in their respective private
source repositories.

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
