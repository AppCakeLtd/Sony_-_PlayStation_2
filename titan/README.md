# TITAN device integration

This fork serves PS2 game artwork to TITAN handhelds. Files under `titan/`
are ours; everything else stays merge-syncable with upstream
libretro-thumbnails.

- `serials-boxarts.json`: **GameID (serial) → boxart filename**.
  - The device reads a disc's serial from its `SYSTEM.CNF`
    (`BOOT2 = cdrom0:\SCUS_973.28;1` → `SCUS-97328`), or from an Open PS2
    Loader file name for compressed images.
  - It looks the serial up here and fetches `Named_Boxarts/<filename>`, plus
    the same name from `Named_Snaps` and `Named_Titles` where they exist.
  - Lookups are exact; there is no name matching on the device.
    Thumbnail names drift across Redump revisions, so that matching happens
    offline in the generator, where its output can be audited.
- `generate-mapping.py` regenerates the JSON from libretro-database's PS2
  Redump dat, joined against the actual `Named_Boxarts/` tree.
  - It reads the tree from git, so a blob-less partial clone is enough.
  - Run it after each upstream sync.
  - Curated fixes go in `MANUAL_EXTRA`, or edit the JSON directly via a PR.

Thumbnails that are git symlinks are resolved to their real file by the
generator: raw GitHub serves a symlink as text, never the image.

Coverage at generation (2026-10-05): 10,401 of 12,909 serials mapped,
reaching 8,196 of 8,502 boxart files (23 mappings resolved through symlinks). 200 of those mappings come from the
region-subset rule (a `(USA)` print for a `(USA, Canada)` release). Unmapped
serials fall back to the UI's generated cover.
