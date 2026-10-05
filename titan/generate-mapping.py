#!/usr/bin/env python3
# Regenerate titan/serials-boxarts.json — the GameID (serial) -> boxart
# filename mapping the TITAN device fetches PS2 art through. Text-name
# matching on-device fails (thumbnail names drift across Redump revisions);
# this join runs OFFLINE where its output is auditable, and the device does
# exact dictionary lookups only. The same filename serves Named_Snaps and
# Named_Titles where those exist.
#
# Sources:
#   1. libretro-database metadat/redump — Redump full names + serials
#      (fetched live)
#   2. this repo's Named_Boxarts tree — ground truth of existing files, read
#      from git (works in a blob-less partial clone: names only, no images)
#
# Join, first tier that matches wins:
#   1. exact sanitized-name match;
#   2. normalized (base title + region set, language/version tags ignored),
#      unambiguous candidates only; version variants collapse to the base print;
#   3. region subset: a print whose regions are a subset of the release's
#      (Redump renamed "(USA)" releases to "(USA, Canada)"; the thumbnail
#      kept "(USA)"), again unambiguous only.
#
# Usage:  python3 titan/generate-mapping.py   (from the repo root; needs
# network; overwrites titan/serials-boxarts.json). Run after every upstream
# thumbnails sync. The generator preserves nothing: fold manual fixes into
# MANUAL_EXTRA below.
import json, re, subprocess, urllib.request, os, sys

RAW = "https://raw.githubusercontent.com/libretro/libretro-database/master/metadat"
DAT_REDUMP = f"{RAW}/redump/Sony%20-%20PlayStation%202.dat"

# Serial -> filename entries curated by hand (win over generated ones).
MANUAL_EXTRA = {}

REGIONS = {'USA', 'Europe', 'Japan', 'Asia', 'Australia', 'Korea', 'UK', 'Germany',
           'France', 'Italy', 'Spain', 'Russia', 'World', 'Scandinavia',
           'Latin America', 'Canada', 'Netherlands', 'Poland', 'Austria', 'Switzerland',
           'China', 'Taiwan', 'Brazil', 'Greece', 'Portugal', 'Sweden', 'Denmark',
           'Norway', 'Finland', 'Belgium', 'India'}

san = lambda n: re.sub(r'[&*/:`<>?\\|"]', '_', n)

def keyof(name):
    groups = re.findall(r'\(([^)]*)\)', name)
    title = re.sub(r'\s*\([^)]*\)', '', name).strip().lower()
    regs = frozenset(r.strip() for g in groups for r in g.split(',') if r.strip() in REGIONS)
    return (title, regs)

def fetch(url):
    return urllib.request.urlopen(url).read().decode('utf-8')

def tree_files(root, sub):
    out = subprocess.check_output(['git', '-C', root, 'ls-tree', '--name-only', 'HEAD', sub + '/'],
                                  text=True)
    return sorted(os.path.basename(l) for l in out.splitlines() if l.endswith('.png'))

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = tree_files(root, 'Named_Boxarts')

    entries = {}
    for name, serial in re.findall(r'game \(\s*\n\tname "([^"]+)"(?:\n\tregion "[^"]*")?\n\tserial "([^"]+)"',
                                   fetch(DAT_REDUMP)):
        entries.setdefault(serial, name)

    art_by_key, art_by_title = {}, {}
    for f in files:
        k = keyof(f[:-4])
        art_by_key.setdefault(k, []).append(f)
        art_by_title.setdefault(k[0], []).append((k[1], f))

    def pick(cands):
        if not cands:
            return None
        if len(cands) == 1:
            return cands[0]
        unversioned = [c for c in cands if not re.search(r'\(v[\d.]+\)', c)]
        if len(unversioned) == 1:
            return unversioned[0]
        if not unversioned:
            return sorted(cands)[-1]
        return None                          # genuinely ambiguous — skip

    fileset = set(files)
    mapping, ambiguous, by_subset = {}, [], 0
    for serial, name in entries.items():
        fn = san(name) + '.png'
        title, regs = keyof(name)
        cands = art_by_key.get((title, regs), [])
        if fn in fileset:
            mapping[serial] = fn
            continue
        c = pick(cands)
        if c:
            mapping[serial] = c
            continue
        sub = [f for r, f in art_by_title.get(title, []) if r and r < regs] if not cands else []
        c = pick(sub)
        if c:
            mapping[serial] = c
            by_subset += 1
        elif cands or sub:
            ambiguous.append((serial, name))
    mapping.update(MANUAL_EXTRA)

    out = os.path.join(root, 'titan', 'serials-boxarts.json')
    json.dump(mapping, open(out, 'w'), indent=1, sort_keys=True)
    reached = len(set(mapping.values()))
    print(f"serials: {len(entries)}  mapped: {len(mapping)} ({by_subset} by region subset)  "
          f"ambiguous skipped: {len(ambiguous)}")
    print(f"art files reached: {reached} of {len(files)}")
    for s, n in ambiguous:
        print(f"  AMBIGUOUS {s}  {n}", file=sys.stderr)

if __name__ == '__main__':
    main()
