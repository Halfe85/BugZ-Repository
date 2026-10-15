# BugZ Kodi repository

## Install

1. Download `kodi/repository.bugz/repository.bugz-1.0.0.zip` from GitHub to storage
   Kodi can access. Keep it zipped.
2. In Kodi, enable Settings > System > Add-ons > Unknown sources if needed.
3. Use Add-ons > Install from zip file to install the downloaded repository ZIP.
4. Open Install from repository > BugZ Kodi Repository > Video add-ons > Otaku.
5. Install/update Otaku, restart Kodi, enable AnimePahe, and rescrape an episode.

The addon ID remains plugin.video.otaku and settings remain in the active Kodi
profile. The published custom version is 5.3.3+bugz.3. Required context.otaku is
indexed here and downloaded from its upstream Hooty distribution. Kodi's normal addon dependency installer handles
beautifulsoup4, inputstreamhelper, and pyqrcode using configured repositories.
The repository uses a Kodi 20+ directory because Otaku requires xbmc.python 3.0.1.

If another repository publishes a newer Otaku release, select the BugZ version
in Otaku's Versions list to stay on this modified build. Automatic updates can
be disabled for Otaku if desired; newer upstream releases may replace the changes.

## Logging

special://profile/addon_data/plugin.video.otaku/animepahe-megaplay.log

Add special://profile/addon_data/plugin.video.otaku/ as a Kodi File manager source
if you need to copy out the log. Requests, source decoding, subtitle selection,
source counts, and exceptions are recorded independently of Kodi's debug setting.
Cookie and authorization header values are redacted.

## Packages and verification

- kodi/addons.xml: Kodi catalog for repository.bugz and plugin.video.otaku.
- kodi/dependencies.xml: context.otaku catalog pointing to the upstream Hooty ZIP.
- kodi/addons.xml.md5: change-detection checksum of the exact catalog bytes.
- kodi/SHA256SUMS and package .sha256 files: package integrity checks.
- repository.bugz/addon.xml: repository installer source definition.

The packages contain addon program files and assets only. No user settings,
account credentials, addon databases, watchlists, or diagnostic logs are packaged.
Original Otaku authorship and GPL-3.0 declarations are retained. The complete
Python addon source is available inside its installable ZIP.

ZIP integrity, XML agreement, asset availability, and Python 3.8 syntax are checked
locally. These checks do not establish installation or playback on a Shield.
The previous live provider checks are historical; this packaging task has not
rerun current Megaplay playback requests.

## Rebuild locally

The initial local snapshot is in Otaku-modified/_local/source/ and is ignored by
Git. Rebuild it with:

    python tools/build_kodi_repo.py

On a fresh clone, capture the current installed addons first:

    python tools/build_kodi_repo.py --capture-installed /path/to/.kodi/addons

For a subsequent custom release, increment --otaku-version, keep old published
ZIPs, rebuild the catalog, and publish the changed artifacts. The installed Kodi
addon is never altered by this build script. Keep the Jellyfin manifest.json and
packages/ distribution separate from the Kodi catalog.

Kodi references:
- https://kodi.wiki/view/Add-on_repositories
- https://kodi.wiki/view/Add-on_manager#How_to_install_from_a_ZIP_file

Startup delay: once Kodi signals that the video is loaded, Otaku holds it paused
for three seconds and resumes the same video. Stop, shutdown, and an early manual
resume cancel the automatic hold. This applies to standard and widget/context
playback. A few initial frames may precede Kodi's AV-ready notification; the
three-second hold is not a hardware display-ready signal. Shield verification
is still required.

Run `python tools/test_startup_delay.py -v` to verify the pause/resume state
transitions and both resolver handoffs. On a fresh clone the tests read the
published ZIP. A bugz.2 rebuild requires its modified source; the build refuses
to label older source as bugz.2.

## AniList metadata recovery

Show details come from https://graphql.anilist.co. Empty or non-JSON responses
previously raised an exception while opening a show. Transient failures now
have at most two retries with abort-aware waits. Long Retry-After cooldowns
are not retried immediately, and failed results are not cached. Existing show
metadata is reused where available; otherwise Otaku displays an unavailable
message and finishes the show folder without writing watch progress.

Failed responses are recorded in
`special://profile/addon_data/plugin.video.otaku/anilist-metadata.log`, including
status, content type, attempt, reason, and up to 512 characters of response body.
No authentication headers are recorded. The original failing response was not
saved, so its exact server-side cause remains unknown. Live retries through
Otaku's actual HTTP client succeeded during investigation.

Run `python tools/test_anilist_metadata.py -v` for recovery and caller regressions.
A bugz.3 rebuild requires its modified source (extract the published ZIP into
_local/source/ or capture an installed bugz.3 addon).
