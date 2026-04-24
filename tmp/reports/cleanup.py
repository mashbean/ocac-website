#!/usr/bin/env python3
"""Cleanup pass for auto-generated archive articles.

1) Dedup: group files by normalized title; keep the one with the longest body; delete the rest (zh+en pair).
2) Rewrite bodies: join PDF line-wrap artefacts into proper paragraphs; preserve structured meta lines.
3) Remove low-content articles (no meaningful body, only boilerplate titles).

Does NOT touch report-*.md or project-*.md — those are manually authored.
"""
from pathlib import Path
import re, unicodedata

ROOT = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo")
ZH = ROOT / "content/zh/archive"
EN = ROOT / "content/en/archive"

KEY_PATTERNS = [
    "主辦", "協辦", "合辦", "合作夥伴", "策劃", "策展", "策展人",
    "時間", "地點", "時間和地點", "時間與地點", "活動性質", "參與者",
    "與談", "與談單位", "進駐藝術家", "放映", "演出", "展覽", "補助",
    "執行時間", "執行計畫", "總參與人數", "邀請藝術家", "藝術家",
    "會議主持人", "主持人", "地主", "協作者", "導讀", "來訪者", "受訪者",
    "Organiser", "Organizer", "Co-organizer", "Co-curator", "Curator",
    "Time", "Venue", "Date", "Location", "Participants", "With",
]
# Quick key-line detector: matches starts like "主辦|..." or "主辦：..." or "主辦 |"
KEY_LINE_RE = re.compile(r"^\s*(" + "|".join(re.escape(k) for k in KEY_PATTERNS) + r")\s*[\|｜:：]", re.I)
# Markdown heading / image / list markers that should not be joined
SPECIAL_LINE_RE = re.compile(r"^\s*(#+\s|!\[|---|\*|-\s)")
# End-of-sentence characters (Chinese + Latin)
END_PUNCT = set("。！？!?;；")

def norm_title(t):
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"[\|｜/,.，。、·\-—–_\(\)（）\[\]【】<>「」『』:：;；!！?？]", "", t)
    return t.lower()

def parse_file(path: Path):
    t = path.read_text()
    if not t.startswith("---\n"):
        return None
    m = re.search(r"\n---\n", t[4:])
    if not m:
        return None
    fm_end = 4 + m.start() + 1
    fm = t[4:fm_end]
    body = t[fm_end + 4:]
    # Extract title
    mt = re.search(r'^title:\s*"([^"]*)"', fm, re.M)
    title = mt.group(1) if mt else ""
    return {"path": path, "fm": fm, "body": body, "title": title}

# ---------- Step 1: dedup ----------
def is_new_generated(p: Path) -> bool:
    """Returns True if file is one of the auto-generated archive articles from 2020-2025.

    Exclude: report-*.md, project-*.md (curated), _index.md, old K2 patterns.
    Include: 2020-*.md..2025-*.md where the slug part is a generated label.
    """
    name = p.name
    if name.startswith("report-") or name.startswith("project-"):
        return False
    if name == "_index.md":
        return False
    if not re.match(r"^(2020|2021|2022|2023|2024|2025)-", name):
        return False
    # Exclude old K2 YYYY-MM-DD-HH-MM-SS pattern
    if re.match(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}", name):
        return False
    return True

def dedup():
    # Group zh files by normalized title; en paired by filename (same key)
    zh_files = [p for p in ZH.iterdir() if p.is_file() and is_new_generated(p)]
    groups = {}
    for f in zh_files:
        info = parse_file(f)
        if not info:
            continue
        key = norm_title(info["title"])
        if not key:
            # Remove files with empty/junk title
            continue
        groups.setdefault(key, []).append(info)

    deleted = []
    for key, files in groups.items():
        if len(files) < 2:
            continue
        # Keep the one with longest body; delete rest
        files.sort(key=lambda x: -len(x["body"]))
        keep = files[0]
        for f in files[1:]:
            # delete zh + en counterpart
            zh_path = f["path"]
            en_path = EN / zh_path.name
            if zh_path.exists():
                zh_path.unlink()
                deleted.append(zh_path.name)
            if en_path.exists():
                en_path.unlink()
                deleted.append(en_path.name + " (en)")
    return deleted

# ---------- Step 2: rewrite bodies ----------
def rewrite_body(body: str) -> str:
    """Join PDF-wrap artefacts while preserving structured meta + paragraph breaks."""
    # Strip the auto-generation trailer; we’ll re-add a lighter version
    body = re.sub(r"\n+---\n+\*本文由[^*]+\*\n*$", "", body)
    body = re.sub(r"\n+---\n+\*Auto-generated from[^*]+\*\n*$", "", body)
    body = re.sub(r"\n+---\n+\*This article[^*]+\*\n*$", "", body)

    # Split into logical blocks (blank-line separated)
    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]

    # Join policy: merge consecutive blocks unless:
    #   - Next block starts with KEY_LINE or special marker
    #   - Current block ends with sentence-end punctuation
    #   - Next block starts with a list marker (- ) or heading
    merged = []
    cur = ""
    for blk in raw_blocks:
        first_line = blk.split("\n", 1)[0]
        is_key = bool(KEY_LINE_RE.match(first_line))
        is_special = bool(SPECIAL_LINE_RE.match(first_line))
        is_heading = first_line.startswith("#")

        if not cur:
            cur = blk
            continue

        # Decide whether to join
        cur_last_ch = cur.rstrip()[-1] if cur.rstrip() else ""
        cur_starts_key = bool(KEY_LINE_RE.match(cur.split("\n", 1)[0]))
        cur_starts_special = bool(SPECIAL_LINE_RE.match(cur.split("\n", 1)[0]))

        # Always break for headings / images / lists in next block
        if is_heading or is_special:
            merged.append(cur)
            cur = blk
            continue
        # Start of a new key line → new paragraph
        if is_key:
            merged.append(cur)
            cur = blk
            continue
        # If the current chunk ended a sentence, start fresh
        if cur_last_ch in END_PUNCT:
            merged.append(cur)
            cur = blk
            continue
        # If current starts with key but this block starts plain, it's a continuation of the key value → join on same line
        if cur_starts_key and not is_key:
            cur = cur.rstrip() + " " + blk.lstrip()
            continue
        # Plain prose continuation → join without extra space between CJK
        cur_end = cur.rstrip()[-1] if cur.rstrip() else ""
        blk_start = blk.lstrip()[0] if blk.lstrip() else ""
        if ("\u4e00" <= cur_end <= "\u9fff") and ("\u4e00" <= blk_start <= "\u9fff"):
            cur = cur.rstrip() + blk.lstrip()
        else:
            cur = cur.rstrip() + " " + blk.lstrip()
    if cur:
        merged.append(cur)

    # Also: within a meta block "主辦|xxx\nyyy\nzzz", join all subsequent lines (that aren't another key) into one.
    cleaned = []
    for blk in merged:
        first = blk.split("\n", 1)[0]
        if KEY_LINE_RE.match(first):
            lines = blk.split("\n")
            out_lines = [lines[0]]
            for ln in lines[1:]:
                if KEY_LINE_RE.match(ln):
                    out_lines.append(ln)
                else:
                    # Append to last line
                    out_lines[-1] = out_lines[-1].rstrip() + (" " if out_lines[-1] and not out_lines[-1].rstrip().endswith(("、", ",", "，")) else "") + ln.strip()
            cleaned.append("\n".join(out_lines))
        else:
            # Within a prose block, also collapse internal line-wraps
            lines = blk.split("\n")
            coalesced = []
            for ln in lines:
                ln = ln.rstrip()
                if not coalesced:
                    coalesced.append(ln)
                    continue
                prev = coalesced[-1]
                prev_end = prev[-1] if prev else ""
                this_start = ln.lstrip()[0] if ln.lstrip() else ""
                if prev_end in END_PUNCT:
                    coalesced.append(ln)
                elif prev.startswith(("#", "!", "-", "*", "|")):
                    coalesced.append(ln)
                elif ln.startswith(("#", "!", "-", "*", "|")):
                    coalesced.append(ln)
                else:
                    # join
                    if ("\u4e00" <= prev_end <= "\u9fff") and ("\u4e00" <= this_start <= "\u9fff"):
                        coalesced[-1] = prev + ln.lstrip()
                    else:
                        coalesced[-1] = prev + " " + ln.lstrip()
            cleaned.append("\n".join(coalesced))

    return "\n\n".join(cleaned).strip()

def rewrite_file(path: Path, lang: str):
    info = parse_file(path)
    if not info:
        return False
    new_body = rewrite_body(info["body"])
    # Re-attach a lighter trailer
    year_m = re.search(r"^(2020|2021|2022|2023|2024|2025)-", path.name)
    year = year_m.group(1) if year_m else ""
    trailer_zh = f"\n\n---\n\n*本文由 {year} 年度結案報告整理；文字、圖片對應仍在校正中。*\n"
    trailer_en = f"\n\n---\n\n*Compiled from OCAC’s {year} annual closing report; text and image matching are being refined.*\n"
    trailer = trailer_zh if lang == "zh" else trailer_en
    new_text = "---\n" + info["fm"] + "\n---\n" + new_body + trailer
    if new_text != path.read_text():
        path.write_text(new_text)
        return True
    return False

def rewrite_all():
    n = 0
    for base, lang in [(ZH, "zh"), (EN, "en")]:
        for p in base.iterdir():
            if not p.is_file() or not is_new_generated(p):
                continue
            if rewrite_file(p, lang):
                n += 1
    return n

# ---------- Step 3: remove low-content stubs ----------
def remove_low_content():
    """Delete stubs whose title is boilerplate cover-page (e.g. '2023 執行成果', 'A-3 年度營運計畫')."""
    junk_patterns = [
        r"^\d{4}\s*執行成果$",
        r"^\d{4}\s*年\s*度?\s*執行成果",
        r"^\d{4}\s*年\s*度?\s*執行\s*成果\s*總\s*表",
        r"^A-\d\s*",
        r"^\(A-\d",
        r"^年度計畫",
        r"^Annual Report$",
    ]
    deleted = []
    for base, lang in [(ZH, "zh"), (EN, "en")]:
        for p in list(base.iterdir()):
            if not p.is_file() or not is_new_generated(p):
                continue
            info = parse_file(p)
            if not info:
                continue
            t = info["title"]
            for pat in junk_patterns:
                if re.search(pat, t):
                    p.unlink()
                    deleted.append(p.name)
                    break
    return deleted

if __name__ == "__main__":
    print("=== Step 3: remove low-content / cover-page stubs ===")
    d = remove_low_content()
    print(f"  deleted {len(d)}")
    for x in d[:20]:
        print("  -", x)

    print("\n=== Step 1: dedup by normalized title ===")
    d = dedup()
    print(f"  deleted {len(d)}")
    for x in d[:20]:
        print("  -", x)

    print("\n=== Step 2: rewrite bodies ===")
    n = rewrite_all()
    print(f"  rewrote {n}")
