#!/usr/bin/env python3
"""
OCAC Google Drive → Hugo 同步腳本（雙語版）

Drive 結構：
  OCAC網站更新與協作/
  ├── archive/<slug 資料夾>/content（Google Doc）+ images/
  ├── artists/<slug 資料夾>/content（Google Doc）+ images/
  └── artspaces/<slug 資料夾>/content（Google Doc）+ images/

每篇文章以中英文同框格式撰寫，同步時拆為：
  content/zh/<section>/<slug>.md
  content/en/<section>/<slug>.md

用法：
  python scripts/gdrive_sync.py                  # 同步全部
  python scripts/gdrive_sync.py --dry-run        # 預覽，不寫入
  python scripts/gdrive_sync.py --section archive
"""

import argparse
import io
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ── 設定區 ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
CONTENT_DIR = REPO_ROOT / "content"
STATIC_IMAGES_DIR = REPO_ROOT / "static" / "images" / "gdrive"
CREDENTIALS_FILE = REPO_ROOT / "scripts" / "gdrive_credentials.json"
TOKEN_FILE = REPO_ROOT / "scripts" / "gdrive_token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Google Drive 根資料夾 ID（設定環境變數 GDRIVE_ROOT_FOLDER_ID）
GDRIVE_ROOT_FOLDER_ID = os.environ.get("GDRIVE_ROOT_FOLDER_ID", "")

SECTIONS = ["archive", "artists", "artspaces"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# 跳過這些前綴開頭的資料夾或文件（範本、說明）
SKIP_PREFIXES = ("📋", "📌", "_")


# ── Google Drive 授權 ─────────────────────────────────────────────────────────

def get_drive_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(
                    f"[錯誤] 找不到 {CREDENTIALS_FILE}\n"
                    "請先執行 python scripts/gdrive_auth.py 完成授權設定。"
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


# ── Drive 檔案操作 ────────────────────────────────────────────────────────────

def list_children(service, folder_id: str) -> List[dict]:
    results, page_token = [], None
    while True:
        resp = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
            )
            .execute()
        )
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results


def find_folder_id(service, parent_id: str, name: str) -> Optional[str]:
    for item in list_children(service, parent_id):
        if item["name"] == name and item["mimeType"] == "application/vnd.google-apps.folder":
            return item["id"]
    return None


def download_bytes(service, file_id: str) -> bytes:
    req = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()


def export_doc_as_text(service, file_id: str) -> str:
    """Export a Google Doc as plain text (UTF-8)."""
    req = service.files().export_media(fileId=file_id, mimeType="text/plain")
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    # Strip BOM if present
    return buf.getvalue().decode("utf-8").lstrip("﻿")


def get_content_text(service, file: dict) -> str:
    if file["mimeType"] == "application/vnd.google-apps.document":
        return export_doc_as_text(service, file["id"])
    return download_bytes(service, file["id"]).decode("utf-8").lstrip("﻿")


def find_content_file(children: List[dict]) -> Optional[dict]:
    """Find the main content file in an article folder (Google Doc or content.md)."""
    for f in children:
        name = f["name"]
        if (
            f["mimeType"] == "application/vnd.google-apps.document"
            and not any(name.startswith(p) for p in SKIP_PREFIXES)
        ):
            return f
    for f in children:
        if f["name"].lower() == "content.md":
            return f
    return None


# ── Slug 工具 ─────────────────────────────────────────────────────────────────

def to_slug(name: str) -> str:
    slug = Path(name).stem.lower().strip()
    slug = re.sub(r"[^\w一-鿿\-]+", "-", slug)
    return re.sub(r"-{2,}", "-", slug).strip("-")


def img_web_path(section: str, slug: str, filename: str) -> str:
    return f"/images/gdrive/{section}/{slug}/{filename}"


def yaml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ── 模板解析 ──────────────────────────────────────────────────────────────────

def parse_field(text: str, *labels: str) -> str:
    """Extract a single-line field value. Strips parenthetical hints like （格式：…）."""
    for label in labels:
        m = re.search(rf"^{re.escape(label)}\s*[：:]\s*(.+)?$", text, re.MULTILINE)
        if m:
            value = (m.group(1) or "").strip()
            # Remove inline hint text in full-width parentheses
            value = re.sub(r"（[^）]{0,30}）", "", value).strip()
            if value:
                return value
    return ""


def parse_multiline_field(text: str, *labels: str) -> List[str]:
    """Extract a list of image filenames from a multi-line field."""
    for label in labels:
        m = re.search(rf"^{re.escape(label)}\s*[：:]\s*(.*)$", text, re.MULTILINE)
        if not m:
            continue
        lines = []
        first = re.sub(r"（[^）]{0,30}）", "", m.group(1)).strip()
        if first and Path(first).suffix.lower() in IMAGE_EXTENSIONS:
            lines.append(first)
        for line in text[m.end():].splitlines():
            s = re.sub(r"（[^）]{0,30}）", "", line).strip()
            if not s:
                continue
            if re.match(r"^[━─]{3}", s) or re.search(r"[：:]\s*", s):
                break
            if Path(s).suffix.lower() in IMAGE_EXTENSIONS:
                lines.append(s)
        return lines
    return []


def parse_section_content(text: str, header: str) -> str:
    """
    Extract free-form content under a named section header.
    Stops at the next ━━━ divider.
    Skips hint lines starting with '提示：' or 'Tip:'.
    """
    m = re.search(rf"^{re.escape(header)}\s*$", text, re.MULTILINE)
    if not m:
        return ""

    lines = text[m.end():].splitlines()
    content_lines: List[str] = []
    started = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^━{3,}", stripped):
            break
        if re.match(r"^(提示|Tip)[：:]", stripped):
            started = True
            continue
        if not started and not stripped:
            continue
        started = True
        content_lines.append(line)

    while content_lines and not content_lines[-1].strip():
        content_lines.pop()

    return "\n".join(content_lines).strip()


def expand_image_paths(content: str, section: str, slug: str) -> str:
    """
    將內文中的短檔名圖片引用補全為完整的 Hugo 路徑。
    ![](photo.jpg) → ![](/images/gdrive/section/slug/photo.jpg)
    已是完整路徑（/ 開頭）的引用保持不變。
    """
    def replace(m: re.Match) -> str:
        alt = m.group(1)
        src = m.group(2).strip()
        if src.startswith("/") or src.startswith("http"):
            return m.group(0)  # 已是完整路徑，不動
        ext = Path(src).suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            return m.group(0)  # 不是圖片副檔名，不動
        return f"![{alt}]({img_web_path(section, slug, src)})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, content)


# ── Hugo Markdown 生成 ────────────────────────────────────────────────────────

def make_archive_md(text: str, slug: str, section: str, lang: str, available_images: Optional[Set[str]] = None) -> str:
    available_images = available_images or set()
    zh_title = parse_field(text, "標題（中文）", "標題")
    en_title = parse_field(text, "Title（English）", "Title")
    _date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    date_str = parse_field(text, "開始日期")
    if not _date_pattern.match(date_str):
        date_str = ""
    end_date_str = parse_field(text, "結束日期（跨日才填）", "結束日期")
    if not _date_pattern.match(end_date_str):
        end_date_str = ""
    year_tag = parse_field(text, "年份標籤")
    extra_tags_str = parse_field(text, "標籤")
    people_str = parse_field(text, "參與人員")
    projects_str = parse_field(text, "相關計畫")
    cover = parse_field(text, "首圖檔名") or ("cover.jpg" if "cover.jpg" in available_images else "")
    thumbnail = parse_field(text, "卡片縮圖檔名") or ("thumb.jpg" if "thumb.jpg" in available_images else "")
    body_images = parse_multiline_field(text, "內文圖片")

    title = zh_title if lang == "zh" else en_title
    content_header = "中文內容" if lang == "zh" else "English Content"
    content = parse_section_content(text, content_header)
    content = expand_image_paths(content, section, slug)

    if body_images:
        img_md = "\n\n".join(f"![]({img_web_path(section, slug, f)})" for f in body_images)
        content = f"{content}\n\n{img_md}".strip()

    fm = f'---\ntitle: "{yaml_escape(title)}"\n'
    if date_str:
        fm += f'date: "{date_str}T00:00:00+08:00"\n'
    if end_date_str:
        fm += f'endDate: "{end_date_str}T00:00:00+08:00"\n'
    fm += 'draft: false\nsection: "archive"\n'
    if cover:
        fm += f'image: "{img_web_path(section, slug, cover)}"\n'
    if thumbnail:
        fm += f'thumbnail: "{img_web_path(section, slug, thumbnail)}"\n'
    all_tags = [year_tag] if year_tag else []
    if extra_tags_str:
        all_tags += [t.strip() for t in re.split(r"[,，、]", extra_tags_str) if t.strip()]
    tags_yaml = "[" + ", ".join(f'"{yaml_escape(t)}"' for t in all_tags) + "]"
    fm += f"tags: {tags_yaml}\n"
    if people_str:
        people = [t.strip() for t in re.split(r"[,，、]", people_str) if t.strip()]
        fm += "people: [" + ", ".join(f'"{yaml_escape(p)}"' for p in people) + "]\n"
    if projects_str:
        projects = [t.strip() for t in re.split(r"[,，、]", projects_str) if t.strip()]
        fm += "projects: [" + ", ".join(f'"{yaml_escape(p)}"' for p in projects) + "]\n"
    fm += "---\n\n"

    return fm + content


def make_artists_md(text: str, slug: str, section: str, lang: str, available_images: Optional[Set[str]] = None) -> str:
    available_images = available_images or set()
    zh_name = parse_field(text, "姓名（中文）", "姓名")
    en_name = parse_field(text, "Name（English）", "Name")
    nationality = parse_field(text, "國籍 / Nationality", "國籍", "Nationality")
    portrait = parse_field(text, "個人照檔名") or ("cover.jpg" if "cover.jpg" in available_images else "")
    thumbnail = parse_field(text, "卡片縮圖檔名") or ("thumb.jpg" if "thumb.jpg" in available_images else "")
    date_str = parse_field(text, "新增日期")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        date_str = ""
    extra_tags_str = parse_field(text, "標籤")
    projects_str = parse_field(text, "相關計畫")

    title = zh_name if lang == "zh" else en_name
    content_header = "中文介紹" if lang == "zh" else "English Bio"
    content = parse_section_content(text, content_header)
    content = expand_image_paths(content, section, slug)

    fm = f'---\ntitle: "{yaml_escape(title)}"\n'
    if date_str:
        fm += f'date: "{date_str}T00:00:00+08:00"\n'
    fm += f'draft: false\nsection: "artists"\nalias: "{slug}"\n'
    if nationality:
        fm += f'nationality: "{yaml_escape(nationality)}"\n'
    if portrait:
        fm += f'image: "{img_web_path(section, slug, portrait)}"\n'
    if thumbnail:
        fm += f'thumbnail: "{img_web_path(section, slug, thumbnail)}"\n'
    if extra_tags_str:
        extra_tags = [t.strip() for t in re.split(r"[,，、]", extra_tags_str) if t.strip()]
        tags_yaml = "[" + ", ".join(f'"{yaml_escape(t)}"' for t in extra_tags) + "]"
        fm += f"tags: {tags_yaml}\n"
    # 藝術家自身帶上自己的 slug 作為 people，讓 archive 文章能找到此頁
    fm += f'people: ["{slug}"]\n'
    if projects_str:
        projects = [t.strip() for t in re.split(r"[,，、]", projects_str) if t.strip()]
        fm += "projects: [" + ", ".join(f'"{yaml_escape(p)}"' for p in projects) + "]\n"
    fm += "---\n\n"

    return fm + content


def make_artspaces_md(text: str, slug: str, section: str, lang: str, available_images: Optional[Set[str]] = None) -> str:
    available_images = available_images or set()
    zh_name = parse_field(text, "空間名稱（中文）", "空間名稱")
    en_name = parse_field(text, "Space Name（English）", "Space Name")
    country = parse_field(text, "國家 / Country", "國家", "Country")
    city = parse_field(text, "城市 / City", "城市", "City")
    cover = parse_field(text, "封面圖檔名") or ("cover.jpg" if "cover.jpg" in available_images else "")
    thumbnail = parse_field(text, "卡片縮圖檔名") or ("thumb.jpg" if "thumb.jpg" in available_images else "")
    date_str = parse_field(text, "新增日期")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        date_str = ""
    extra_tags_str = parse_field(text, "標籤")
    people_str = parse_field(text, "相關人員")
    projects_str = parse_field(text, "相關計畫")

    title = zh_name if lang == "zh" else en_name
    content_header = "中文介紹" if lang == "zh" else "English Description"
    content = parse_section_content(text, content_header)
    content = expand_image_paths(content, section, slug)

    fm = f'---\ntitle: "{yaml_escape(title)}"\n'
    if date_str:
        fm += f'date: "{date_str}T00:00:00+08:00"\n'
    fm += f'draft: false\nsection: "artspaces"\nalias: "{slug}"\n'
    if country:
        fm += f'country: "{yaml_escape(country)}"\n'
    if city:
        fm += f'city: "{yaml_escape(city)}"\n'
    if cover:
        fm += f'image: "{img_web_path(section, slug, cover)}"\n'
    if thumbnail:
        fm += f'thumbnail: "{img_web_path(section, slug, thumbnail)}"\n'
    if extra_tags_str:
        extra_tags = [t.strip() for t in re.split(r"[,，、]", extra_tags_str) if t.strip()]
        tags_yaml = "[" + ", ".join(f'"{yaml_escape(t)}"' for t in extra_tags) + "]"
        fm += f"tags: {tags_yaml}\n"
    if people_str:
        people = [t.strip() for t in re.split(r"[,，、]", people_str) if t.strip()]
        fm += "people: [" + ", ".join(f'"{yaml_escape(p)}"' for p in people) + "]\n"
    if projects_str:
        projects = [t.strip() for t in re.split(r"[,，、]", projects_str) if t.strip()]
        fm += "projects: [" + ", ".join(f'"{yaml_escape(p)}"' for p in projects) + "]\n"
    fm += "---\n\n"

    return fm + content


MAKERS = {
    "archive": make_archive_md,
    "artists": make_artists_md,
    "artspaces": make_artspaces_md,
}


# ── 核心同步邏輯 ───────────────────────────────────────────────────────────────

def sync_article(service, section: str, article_folder: dict, dry_run: bool) -> bool:
    """
    同步單篇文章資料夾。Drive 結構：
      <slug-folder>/
        <Google Doc 或 content.md>   ← 必要，雙語格式
        images/                       ← 可選
    輸出：content/zh/<section>/<slug>.md 與 content/en/<section>/<slug>.md
    """
    folder_id = article_folder["id"]
    folder_name = article_folder["name"]
    slug = to_slug(folder_name)
    children = list_children(service, folder_id)

    content_file = find_content_file(children)
    if content_file is None:
        print(f"  [跳過] {section}/{folder_name}：找不到內容文件")
        return False

    text = get_content_text(service, content_file)

    images_folder = next(
        (
            f for f in children
            if f["name"].lower() == "images"
            and f["mimeType"] == "application/vnd.google-apps.folder"
        ),
        None,
    )
    image_files = []
    if images_folder:
        image_files = [
            f for f in list_children(service, images_folder["id"])
            if Path(f["name"]).suffix.lower() in IMAGE_EXTENSIONS
        ]

    available_images = {f["name"].lower() for f in image_files}
    maker = MAKERS[section]
    changed = False

    for lang in ("zh", "en"):
        md_text = maker(text, slug, section, lang, available_images)
        target = CONTENT_DIR / lang / section / f"{slug}.md"

        if dry_run:
            print(f"  [dry-run] 會寫入 {target.relative_to(REPO_ROOT)}")
            changed = True
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            existing = target.read_text("utf-8") if target.exists() else ""
            if existing != md_text:
                target.write_text(md_text, "utf-8")
                changed = True
                print(f"  [更新] {target.relative_to(REPO_ROOT)}")
            else:
                print(f"  [相同] {target.relative_to(REPO_ROOT)}")

    for img in image_files:
        dest = STATIC_IMAGES_DIR / section / slug / img["name"]
        if dry_run:
            print(f"  [dry-run] 會下載圖片 {dest.relative_to(REPO_ROOT)}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                dest.write_bytes(download_bytes(service, img["id"]))
                changed = True
                print(f"  [圖片] {dest.relative_to(REPO_ROOT)}")

    return changed


def sync_section(service, root_id: str, section: str, dry_run: bool) -> Tuple[int, Set[str]]:
    """
    同步一個 section，回傳 (有變更的文章數, Drive 上存在的 slug 集合)。
    支援年份子資料夾（4 位數字）：archive/2025/slug-folder/
    """
    print(f"\n── {section} ──")
    section_folder_id = find_folder_id(service, root_id, section)
    if not section_folder_id:
        print(f"  [跳過] Google Drive 中找不到 '{section}' 資料夾")
        return 0, set()

    article_folders = []
    for item in list_children(service, section_folder_id):
        if item["mimeType"] != "application/vnd.google-apps.folder":
            continue
        if any(item["name"].startswith(p) for p in SKIP_PREFIXES):
            continue
        # 若子資料夾名稱是 4 位數字（年份），進一層取文章資料夾
        if re.match(r"^\d{4}$", item["name"]):
            for child in list_children(service, item["id"]):
                if (
                    child["mimeType"] == "application/vnd.google-apps.folder"
                    and not any(child["name"].startswith(p) for p in SKIP_PREFIXES)
                ):
                    article_folders.append(child)
        else:
            article_folders.append(item)

    if not article_folders:
        print("  （沒有文章資料夾）")
        return 0, set()

    synced_slugs: Set[str] = set()
    total = 0
    for af in article_folders:
        synced_slugs.add(to_slug(af["name"]))
        if sync_article(service, section, af, dry_run):
            total += 1
    return total, synced_slugs


def check_orphans(section: str, synced_slugs: Set[str], dry_run: bool, ci_mode: bool) -> bool:
    """
    找出 Hugo 裡有、但 Drive 上已不存在的文章（可能被誤刪）。
    dry_run 或 ci_mode 下只列出清單，不刪除。
    回傳是否有刪除動作發生。
    """
    orphans: List[Path] = []
    for lang in ("zh", "en"):
        section_dir = CONTENT_DIR / lang / section
        if not section_dir.exists():
            continue
        for md_file in section_dir.glob("*.md"):
            if md_file.stem == "_index":
                continue
            if md_file.stem not in synced_slugs:
                orphans.append(md_file)

    if not orphans:
        return False

    print(f"\n⚠️  偵測到 {len(orphans)} 個文章在 Hugo 裡存在，但 Drive 上找不到對應資料夾：")
    for f in sorted(orphans):
        print(f"   {f.relative_to(REPO_ROOT)}")

    if dry_run:
        print("  → [dry-run] 略過刪除。")
        return False

    if ci_mode:
        print("  → [自動模式] 不執行刪除，請手動確認後處理。")
        return False

    print("\n這些文章可能是在 Drive 上被誤刪，或是尚未匯出到 Drive。")
    print("輸入 'yes' 刪除這些 Hugo 文章；輸入其他任意鍵取消：", end=" ")
    answer = input().strip().lower()
    if answer != "yes":
        print("  → 已取消，文章保留。")
        return False

    for f in orphans:
        f.unlink()
        print(f"  [刪除] {f.relative_to(REPO_ROOT)}")
    return True


# ── Git 操作 ──────────────────────────────────────────────────────────────────

def git_commit_and_push(dry_run: bool):
    os.chdir(REPO_ROOT)
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip():
        print("\n沒有變更，不需要 commit。")
        return
    if dry_run:
        print("\n[dry-run] 有變更，實際執行時會 commit & push。")
        return
    subprocess.run(["git", "add", "content/", "static/images/gdrive/"], check=True)
    subprocess.run(["git", "commit", "-m", "sync: Google Drive 內容更新"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("\n已推送到 GitHub，Cloudflare Pages 部署中…")


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OCAC Google Drive → Hugo 同步")
    parser.add_argument("--dry-run", action="store_true", help="只列出會做的事，不實際寫入")
    parser.add_argument("--section", choices=SECTIONS, default=None, help="只同步指定 section")
    parser.add_argument("--ci", action="store_true", help="CI 模式：不互動，孤兒文章只列出不刪除")
    args = parser.parse_args()

    if not GDRIVE_ROOT_FOLDER_ID:
        print(
            "[錯誤] 請設定環境變數 GDRIVE_ROOT_FOLDER_ID，\n"
            "或在 scripts/gdrive_sync.py 頂部的設定區直接填入資料夾 ID。\n"
            f"新的協作資料夾 ID：179KnBYYrge8Ki8HooHE7eqP2q4AayRIp"
        )
        sys.exit(1)

    service = get_drive_service()
    sections = [args.section] if args.section else SECTIONS

    total_changed = 0
    has_deletion = False

    for section in sections:
        changed, synced_slugs = sync_section(service, GDRIVE_ROOT_FOLDER_ID, section, args.dry_run)
        total_changed += changed
        if check_orphans(section, synced_slugs, args.dry_run, args.ci):
            has_deletion = True

    print(f"\n共有 {total_changed} 篇文章有變更。")
    if total_changed > 0 or has_deletion:
        git_commit_and_push(args.dry_run)


if __name__ == "__main__":
    main()
