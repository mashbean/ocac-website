#!/usr/bin/env python3
"""
OCAC Hugo → Google Drive 反向匯出腳本

將現有 Hugo 內容匯出到 Google Drive，建立雙語協作文件。
每篇文章在 Drive 上產生對應的資料夾與 Google Doc。

Drive 結構：
  OCAC網站更新與協作/
  ├── archive/
  │   └── 2024/
  │       └── 2024-蜿蜒集-台越交流計畫/
  │           └── content（Google Doc，雙語格式）
  ├── artists/
  │   └── chen-chieh-jen/
  │       └── content（Google Doc）
  └── artspaces/
      └── nha-san-collective/
          └── content（Google Doc）

用法：
  python scripts/gdrive_export.py                  # 匯出全部
  python scripts/gdrive_export.py --dry-run        # 預覽，不實際建立
  python scripts/gdrive_export.py --section archive
  python scripts/gdrive_export.py --section archive --year 2024
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import mimetypes
import time

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload

# ── 設定區 ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
CONTENT_DIR = REPO_ROOT / "content"
CREDENTIALS_FILE = REPO_ROOT / "scripts" / "gdrive_credentials.json"
TOKEN_FILE = REPO_ROOT / "scripts" / "gdrive_token.json"

SCOPES = ["https://www.googleapis.com/auth/drive"]  # 需要寫入權限
GDRIVE_ROOT_FOLDER_ID = os.environ.get("GDRIVE_ROOT_FOLDER_ID", "")

SECTIONS = ["archive", "artists", "artspaces"]

# 英文佔位文字的識別特徵（符合其一即視為佔位，清空留白）
EN_STUB_PATTERNS = [
    "auto-generated stub",
    "description pending",
    "### Original Chinese text",
    "Compiled from OCAC",
    "to be refined",
]


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
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


# ── Drive 資料夾操作 ──────────────────────────────────────────────────────────

def get_or_create_folder(service, parent_id: str, name: str) -> str:
    """取得已存在的資料夾 ID，或建立新資料夾。避免重複建立。"""
    resp = (
        service.files()
        .list(
            q=(
                f"'{parent_id}' in parents"
                f" and name = '{name.replace(chr(39), chr(39))}'"
                f" and mimeType = 'application/vnd.google-apps.folder'"
                f" and trashed = false"
            ),
            fields="files(id)",
        )
        .execute()
    )
    files = resp.get("files", [])
    if files:
        return files[0]["id"]
    result = (
        service.files()
        .create(
            body={
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            },
            fields="id",
        )
        .execute()
    )
    return result["id"]


def doc_exists(service, parent_id: str) -> bool:
    """檢查資料夾內是否已有 Google Doc（代表已匯出過）。"""
    resp = (
        service.files()
        .list(
            q=(
                f"'{parent_id}' in parents"
                f" and mimeType = 'application/vnd.google-apps.document'"
                f" and trashed = false"
            ),
            fields="files(id)",
        )
        .execute()
    )
    return bool(resp.get("files"))


def image_exists_in_folder(service, folder_id: str, filename: str) -> bool:
    """檢查 Drive 資料夾內是否已有同名圖片。"""
    safe_name = filename.replace("'", "\\'")
    resp = (
        service.files()
        .list(
            q=(
                f"'{folder_id}' in parents"
                f" and name = '{safe_name}'"
                f" and trashed = false"
            ),
            fields="files(id)",
        )
        .execute()
    )
    return bool(resp.get("files"))


def upload_image_to_folder(service, folder_id: str, local_path: Path) -> str:
    """上傳圖片到 Drive 資料夾，失敗時最多重試 4 次。"""
    mime = mimetypes.guess_type(str(local_path))[0] or "image/jpeg"
    for attempt in range(5):
        try:
            media = MediaFileUpload(str(local_path), mimetype=mime, resumable=False)
            result = (
                service.files()
                .create(
                    body={"name": local_path.name, "parents": [folder_id]},
                    media_body=media,
                    fields="id",
                )
                .execute()
            )
            return result["id"]
        except Exception as e:
            if attempt < 4:
                wait = 2 ** attempt
                print(f"      [重試 {attempt+1}/4] {e} — 等待 {wait}s")
                time.sleep(wait)
            else:
                raise


def create_google_doc(service, parent_id: str, name: str, content: str) -> str:
    """在指定資料夾建立 Google Doc，失敗時最多重試 4 次。"""
    media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="text/plain")
    for attempt in range(5):
        try:
            result = (
                service.files()
                .create(
                    body={
                        "name": name,
                        "mimeType": "application/vnd.google-apps.document",
                        "parents": [parent_id],
                    },
                    media_body=media,
                    fields="id",
                )
                .execute()
            )
            return result["id"]
        except Exception as e:
            if attempt < 4:
                wait = 2 ** attempt
                print(f"    [重試 {attempt+1}/4] {e} — 等待 {wait}s")
                time.sleep(wait)
                media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="text/plain")
            else:
                raise


def collect_article_images(zh_data: dict) -> List[Path]:
    """
    收集文章所有本地圖片：front matter image + 內文所有 ![]() 引用。
    回傳實際存在於本地的 Path 列表（去重、排序）。
    """
    paths: dict[str, Path] = {}  # 用 filename 去重

    def add(image_str: str) -> None:
        if not image_str or "placeholder" in image_str:
            return
        local = REPO_ROOT / "static" / image_str.lstrip("/")
        if local.exists():
            paths[local.name] = local

    # 封面圖
    add(zh_data.get("image", ""))

    # 內文所有圖片
    content = zh_data.get("content", "")
    for m in re.finditer(r"!\[[^\]]*\]\((/images/[^)]+)\)", content):
        add(m.group(1))

    return sorted(paths.values(), key=lambda p: p.name)


def upload_article_images(service, parent_id: str, zh_data: dict) -> None:
    """
    將文章所有圖片上傳到 Drive 的 images/ 子資料夾。
    已存在的圖片自動跳過。
    """
    local_images = collect_article_images(zh_data)
    if not local_images:
        return

    images_folder_id = get_or_create_folder(service, parent_id, "images")
    for local_img in local_images:
        if image_exists_in_folder(service, images_folder_id, local_img.name):
            continue
        try:
            upload_image_to_folder(service, images_folder_id, local_img)
            print(f"    [圖片] 上傳 {local_img.name}")
        except Exception as e:
            print(f"    [圖片錯誤] {local_img.name}: {e}")


# ── Hugo 檔案解析 ─────────────────────────────────────────────────────────────

def parse_hugo_file(path: Path) -> dict:
    """解析 Hugo Markdown 檔案，回傳 front matter 欄位與內文。"""
    text = path.read_text("utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"content": text.strip()}

    fm = parts[1]
    content = parts[2].strip()

    def field(key: str) -> str:
        m = re.search(rf'^{key}:\s*["\']?([^"\'\n]+)["\']?', fm, re.MULTILINE)
        return m.group(1).strip().strip('"\'') if m else ""

    def tags() -> list[str]:
        m = re.search(r'^tags:\s*\[([^\]]*)\]', fm, re.MULTILINE)
        if not m:
            return []
        return [t.strip().strip('"\'') for t in m.group(1).split(",") if t.strip()]

    def extract_date(raw: str) -> str:
        m = re.match(r'"?(\d{4}-\d{2}-\d{2})', raw)
        return m.group(1) if m else ""

    return {
        "title": field("title"),
        "date": extract_date(field("date")),
        "endDate": extract_date(field("endDate")),
        "image": field("image"),
        "tags": tags(),
        "nationality": field("nationality"),
        "country": field("country"),
        "city": field("city"),
        "content": content,
    }


def is_en_stub(content: str) -> bool:
    """判斷英文內容是否為自動產生的佔位文字。"""
    return any(p in content for p in EN_STUB_PATTERNS)


def extract_year(data: dict, slug: str) -> str:
    """從 tags、date 或 slug 中提取年份。"""
    for tag in data.get("tags", []):
        if re.match(r"^\d{4}$", tag):
            return tag
    if data.get("date"):
        return data["date"][:4]
    m = re.match(r"^(\d{4})", slug)
    if m:
        return m.group(1)
    return "未分類"


# ── 雙語文件內容產生 ──────────────────────────────────────────────────────────

DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


def build_archive_doc(zh: dict, en: Optional[dict], slug: str) -> str:
    zh_title = zh.get("title", "")
    en_title = en.get("title", "") if en else ""
    date = zh.get("date", "")
    end_date = zh.get("endDate", "")
    tags = zh.get("tags", [])
    year_tag = tags[0] if tags else ""
    image = zh.get("image", "")
    zh_content = zh.get("content", "")
    en_content = en.get("content", "") if en else ""

    if en_content and is_en_stub(en_content):
        en_content = ""

    if image:
        image_note = [
            f"目前封面圖已上傳至本資料夾的 images/ 子資料夾（檔名：{Path(image).name}）。",
            "可直接替換圖片，或上傳更多圖片作為內文配圖。",
            "新圖片請放入 images/ 資料夾，並在下方「首圖檔名」填入要作為封面的檔名。",
            "",
            f"目前封面圖路徑（參考）：{image}",
            "",
        ]
    else:
        image_note = [
            "請在本資料夾建立 images/ 子資料夾並上傳圖片。",
            "封面圖建議命名為 cover.jpg；內文圖片可自訂檔名。",
            "",
        ]

    lines = [
        "【活動紀錄】",
        "",
        DIVIDER,
        "基本資訊",
        DIVIDER,
        "",
        f"標題（中文）：{zh_title}",
        f"Title（English）：{en_title}",
        f"開始日期：{date}",
        f"結束日期（跨日才填）：{end_date}",
        f"年份標籤：{year_tag}",
        "",
        "",
        DIVIDER,
        "圖片",
        DIVIDER,
        "",
    ] + image_note + [
        "首圖檔名：",
        "卡片縮圖檔名（選填，不填則與首圖相同）：",
        "內文圖片：",
        "",
    ]

    lines += [
        "",
        DIVIDER,
        "中文內容",
        DIVIDER,
        "",
        "提示：可使用 **粗體** 和 *斜體* 等 markdown 格式。",
        "",
        zh_content,
        "",
        "",
        DIVIDER,
        "English Content",
        DIVIDER,
        "",
        "Tip: You can use **bold**, *italic*, and other markdown formatting.",
        "",
        en_content if en_content else "(English description pending — please translate)",
    ]
    return "\n".join(lines)


def build_artists_doc(zh: dict, en: Optional[dict], slug: str) -> str:
    zh_name = zh.get("title", "")
    en_name = en.get("title", "") if en else ""
    nationality = zh.get("nationality", "") or (en.get("nationality", "") if en else "")
    image = zh.get("image", "")
    zh_content = zh.get("content", "")
    en_content = en.get("content", "") if en else ""

    if en_content and is_en_stub(en_content):
        en_content = ""

    if image:
        image_note = [
            f"目前個人照已上傳至本資料夾的 images/ 子資料夾（檔名：{Path(image).name}）。",
            "可直接替換圖片，建議命名為 portrait.jpg。",
            "",
            f"目前圖片路徑（參考）：{image}",
            "",
        ]
    else:
        image_note = [
            "請在本資料夾建立 images/ 子資料夾並上傳個人照，建議命名為 portrait.jpg。",
            "",
        ]

    lines = [
        "【藝術家】",
        "",
        DIVIDER,
        "基本資訊",
        DIVIDER,
        "",
        f"姓名（中文）：{zh_name}",
        f"Name（English）：{en_name}",
        f"國籍 / Nationality：{nationality}",
        "",
        "",
        DIVIDER,
        "圖片",
        DIVIDER,
        "",
    ] + image_note + [
        "個人照檔名：",
        "卡片縮圖檔名（選填，不填則與個人照相同）：",
        "",
    ]

    lines += [
        "",
        DIVIDER,
        "中文介紹",
        DIVIDER,
        "",
        "提示：可使用 **粗體** 和 *斜體* 等 markdown 格式。",
        "",
        zh_content,
        "",
        "",
        DIVIDER,
        "English Bio",
        DIVIDER,
        "",
        "Tip: You can use **bold**, *italic*, and other markdown formatting.",
        "",
        en_content if en_content else "(English bio pending — please translate)",
    ]
    return "\n".join(lines)


def build_artspaces_doc(zh: dict, en: Optional[dict], slug: str) -> str:
    zh_name = zh.get("title", "")
    en_name = en.get("title", "") if en else ""
    country = zh.get("country", "") or (en.get("country", "") if en else "")
    city = zh.get("city", "") or (en.get("city", "") if en else "")
    image = zh.get("image", "")
    zh_content = zh.get("content", "")
    en_content = en.get("content", "") if en else ""

    if en_content and is_en_stub(en_content):
        en_content = ""

    if image:
        image_note = [
            f"目前封面圖已上傳至本資料夾的 images/ 子資料夾（檔名：{Path(image).name}）。",
            "可直接替換圖片，建議命名為 cover.jpg。",
            "",
            f"目前圖片路徑（參考）：{image}",
            "",
        ]
    else:
        image_note = [
            "請在本資料夾建立 images/ 子資料夾並上傳封面圖，建議命名為 cover.jpg。",
            "",
        ]

    lines = [
        "【藝術空間】",
        "",
        DIVIDER,
        "基本資訊",
        DIVIDER,
        "",
        f"空間名稱（中文）：{zh_name}",
        f"Space Name（English）：{en_name}",
        f"國家 / Country：{country}",
        f"城市 / City：{city}",
        "",
        "",
        DIVIDER,
        "圖片",
        DIVIDER,
        "",
    ] + image_note + [
        "封面圖檔名：",
        "卡片縮圖檔名（選填，不填則與封面圖相同）：",
        "",
    ]

    lines += [
        "",
        DIVIDER,
        "中文介紹",
        DIVIDER,
        "",
        "提示：可使用 **粗體** 和 *斜體* 等 markdown 格式。",
        "",
        zh_content,
        "",
        "",
        DIVIDER,
        "English Description",
        DIVIDER,
        "",
        "Tip: You can use **bold**, *italic*, and other markdown formatting.",
        "",
        en_content if en_content else "(English description pending — please translate)",
    ]
    return "\n".join(lines)


BUILDERS = {
    "archive": build_archive_doc,
    "artists": build_artists_doc,
    "artspaces": build_artspaces_doc,
}


# ── 核心匯出邏輯 ──────────────────────────────────────────────────────────────

def export_article(
    service,
    section: str,
    section_folder_id: str,
    slug: str,
    zh_data: dict,
    en_data: Optional[dict],
    year: Optional[str],
    dry_run: bool,
) -> bool:
    """
    匯出單篇文章到 Drive。
    archive 使用年份子資料夾；artists/artspaces 直接在 section 下建立。
    回傳 True 表示實際建立了新文件。
    """
    builder = BUILDERS[section]
    doc_content = builder(zh_data, en_data, slug)

    # 決定父資料夾
    if year:
        year_folder_id = get_or_create_folder(service, section_folder_id, year) if not dry_run else "DRY"
        parent_id = get_or_create_folder(service, year_folder_id, slug) if not dry_run else "DRY"
        path_display = f"{section}/{year}/{slug}"
    else:
        parent_id = get_or_create_folder(service, section_folder_id, slug) if not dry_run else "DRY"
        path_display = f"{section}/{slug}"

    if dry_run:
        imgs = collect_article_images(zh_data)
        img_note = f" + 上傳 {len(imgs)} 張圖片" if imgs else ""
        print(f"  [dry-run] 會建立 {path_display}/content{img_note}")
        return True

    created_doc = False
    if doc_exists(service, parent_id):
        print(f"  [跳過] {path_display}：文件已存在")
    else:
        create_google_doc(service, parent_id, "content", doc_content)
        print(f"  [建立] {path_display}/content")
        created_doc = True

    # 無論文件是否新建，都嘗試上傳所有圖片（已上傳的自動跳過）
    upload_article_images(service, parent_id, zh_data)

    return created_doc


def export_section(
    service,
    root_id: str,
    section: str,
    year_filter: Optional[str],
    dry_run: bool,
) -> int:
    print(f"\n── {section} ──")

    zh_dir = CONTENT_DIR / "zh" / section
    en_dir = CONTENT_DIR / "en" / section

    if not zh_dir.exists():
        print(f"  [跳過] 找不到 {zh_dir}")
        return 0

    zh_files = sorted(
        f for f in zh_dir.glob("*.md") if f.stem != "_index"
    )
    if not zh_files:
        print("  （沒有文章）")
        return 0

    section_folder_id = None
    if not dry_run:
        section_folder_id = get_or_create_folder(service, root_id, section)

    total = 0
    for zh_path in zh_files:
        slug = zh_path.stem
        zh_data = parse_hugo_file(zh_path)

        en_path = en_dir / zh_path.name
        en_data = parse_hugo_file(en_path) if en_path.exists() else None

        year = extract_year(zh_data, slug) if section == "archive" else None

        if year_filter and year != year_filter:
            continue

        if export_article(
            service,
            section,
            section_folder_id,
            slug,
            zh_data,
            en_data,
            year,
            dry_run,
        ):
            total += 1

    return total


# ── 圖片規格說明文件 ──────────────────────────────────────────────────────────

IMAGE_GUIDE_NAME = "📋 圖片規格說明"

IMAGE_GUIDE_CONTENT = """\
📋 圖片規格說明

本文件說明 OCAC 網站各圖片欄位的建議格式與規格。
上傳圖片前請先參考以下規範，有助於維持網站的視覺一致性。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
卡片縮圖格式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

網站列表頁的卡片有三種版型，縮圖比例各不相同。
同一張圖依落在哪個版型，會被自動裁切成不同比例。
若想針對縮圖做特別的構圖，請在文件的「卡片縮圖檔名」欄位單獨指定一張圖。

▌ 直向卡片（Portrait）
  比例：3:4
  建議尺寸：900 × 1200 px
  出現頻率：最常見（每 6 張卡片中出現 3 次）

▌ 橫向卡片（Landscape）
  比例：16:9
  建議尺寸：1600 × 900 px
  出現頻率：每 6 張卡片中出現 1 次

▌ 小卡片（Small）
  比例：1:1（正方形）
  建議尺寸：800 × 800 px
  出現頻率：每 6 張卡片中出現 2 次

注意：卡片落在哪個版型，是依文章的排列順序自動決定，無法手動指定。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
內文首圖（頁首大圖）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

比例：16:9
建議尺寸：1600 × 900 px（頁面顯示最大高度約 440px）
說明：顯示於文章頁面最頂部的橫幅大圖。
      若「首圖檔名」與「卡片縮圖檔名」都沒有填，卡片將不顯示縮圖。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
內文配圖
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

比例：無限制，依實際需求而定
建議寬度：1200 px 以上
說明：嵌入文章內文中，寬度自動填滿文章欄寬。
      在文件中可直接以 ![](檔名.jpg) 方式引用，同步時會自動補全路徑。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
通用建議
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

檔案格式：JPG（照片類）／PNG（含透明背景或圖形類）／WEBP（兼具品質與壓縮）
檔案大小：每張圖片建議壓縮至 500KB 以下，最大不超過 2MB
色彩模式：RGB（請勿使用印刷用的 CMYK）

命名規則：
  • 使用英文小寫 + 數字 + 連字號，避免空格與中文字
  • 範例：cover.jpg、thumb.jpg、photo-01.jpg、portrait.jpg

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
推薦的圖片壓縮工具
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

線上工具（免費）：
  • Squoosh：https://squoosh.app（Google 出品，功能完整）
  • TinyJPG：https://tinyjpg.com（最簡單易用）

桌面工具：
  • ImageOptim（Mac）：https://imageoptim.com
"""


def guide_doc_exists(service, folder_id: str) -> bool:
    """檢查根資料夾內是否已有圖片規格說明文件。"""
    resp = (
        service.files()
        .list(
            q=(
                f"'{folder_id}' in parents"
                f" and name = '{IMAGE_GUIDE_NAME}'"
                f" and mimeType = 'application/vnd.google-apps.document'"
                f" and trashed = false"
            ),
            fields="files(id)",
        )
        .execute()
    )
    return bool(resp.get("files"))


def create_image_guide(service, root_id: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] 會建立圖片規格說明文件")
        return
    if guide_doc_exists(service, root_id):
        print(f"  [跳過] 圖片規格說明：已存在")
        return
    create_google_doc(service, root_id, IMAGE_GUIDE_NAME, IMAGE_GUIDE_CONTENT)
    print(f"  [建立] {IMAGE_GUIDE_NAME}")


# ── 各 section 範本文件 ────────────────────────────────────────────────────────

TEMPLATE_NAME = "📋 新增文章範本"

TEMPLATE_CONTENT = f"""\
📋 新增文章範本

本文件涵蓋三種內容類型的格式：活動紀錄（archive）、藝術家（artists）、藝術空間（artspaces）。

新增文章時，請在對應的 section 資料夾中，建立一個以 slug 命名的子資料夾，
並在其中新增一個名為 content 的 Google Doc，按照以下對應格式填寫。

slug 命名規則：英文小寫 + 數字 + 連字號，避免空格與特殊符號
  範例：2025-terap-festival、chen-chieh-jen、nha-san-collective

圖片請放入該子資料夾的 images/ 子資料夾，規格請參考「📋 圖片規格說明」。


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A. 活動紀錄（archive）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【活動紀錄】

{DIVIDER}
基本資訊
{DIVIDER}

標題（中文）：
Title（English）：
開始日期：（格式：2025-01-01）
結束日期（跨日才填）：（格式：2025-01-03）
年份標籤：（填入 4 位數年份，例如：2025）
標籤：（選填，多個標籤以逗號分隔，例如：lecture, southeast-asia）
參與人員：（選填，填藝術家的資料夾名稱，多人以逗號分隔，例如：chen-chieh-jen, lin-yi-chun）
相關計畫：（選填，填計畫的資料夾名稱，多個以逗號分隔）

{DIVIDER}
圖片
{DIVIDER}

請在本文件所在資料夾建立 images/ 子資料夾並上傳圖片。
封面圖建議命名為 cover.jpg；內文圖片可自訂檔名（英文小寫 + 連字號）。

首圖檔名：
卡片縮圖檔名（選填，不填則與首圖相同）：
內文圖片：

{DIVIDER}
中文內容
{DIVIDER}

提示：可使用 **粗體** 和 *斜體* 等 markdown 格式。
內文插入圖片請使用 ![](檔名.jpg)，同步時會自動補全路徑。

（在此填入中文活動介紹）

{DIVIDER}
English Content
{DIVIDER}

Tip: You can use **bold**, *italic*, and other markdown formatting.
To insert images in the body, use ![](filename.jpg) — paths will be resolved automatically.

(Enter English description here)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
B. 藝術家（artists）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【藝術家】

{DIVIDER}
基本資訊
{DIVIDER}

姓名（中文）：
Name（English）：
國籍 / Nationality：
標籤：（選填，多個標籤以逗號分隔）
相關計畫：（選填，填計畫的資料夾名稱，多個以逗號分隔）

{DIVIDER}
圖片
{DIVIDER}

請在本文件所在資料夾建立 images/ 子資料夾並上傳個人照，建議命名為 portrait.jpg。

個人照檔名：
卡片縮圖檔名（選填，不填則與個人照相同）：

{DIVIDER}
中文介紹
{DIVIDER}

提示：可使用 **粗體** 和 *斜體* 等 markdown 格式。

（在此填入中文藝術家介紹）

{DIVIDER}
English Bio
{DIVIDER}

Tip: You can use **bold**, *italic*, and other markdown formatting.

(Enter English bio here)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C. 藝術空間（artspaces）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【藝術空間】

{DIVIDER}
基本資訊
{DIVIDER}

空間名稱（中文）：
Space Name（English）：
國家 / Country：
城市 / City：
標籤：（選填，多個標籤以逗號分隔）
相關人員：（選填，填藝術家的資料夾名稱，多個以逗號分隔）
相關計畫：（選填，填計畫的資料夾名稱，多個以逗號分隔）

{DIVIDER}
圖片
{DIVIDER}

請在本文件所在資料夾建立 images/ 子資料夾並上傳封面圖，建議命名為 cover.jpg。

封面圖檔名：
卡片縮圖檔名（選填，不填則與封面圖相同）：

{DIVIDER}
中文介紹
{DIVIDER}

提示：可使用 **粗體** 和 *斜體* 等 markdown 格式。

（在此填入中文空間介紹）

{DIVIDER}
English Description
{DIVIDER}

Tip: You can use **bold**, *italic*, and other markdown formatting.

(Enter English description here)
"""


def template_exists(service, root_id: str) -> bool:
    resp = (
        service.files()
        .list(
            q=(
                f"'{root_id}' in parents"
                f" and name = '{TEMPLATE_NAME}'"
                f" and mimeType = 'application/vnd.google-apps.document'"
                f" and trashed = false"
            ),
            fields="files(id)",
        )
        .execute()
    )
    return bool(resp.get("files"))


def create_template(service, root_id: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] 會建立 {TEMPLATE_NAME}")
        return
    if template_exists(service, root_id):
        print(f"  [跳過] {TEMPLATE_NAME}：已存在")
        return
    create_google_doc(service, root_id, TEMPLATE_NAME, TEMPLATE_CONTENT)
    print(f"  [建立] {TEMPLATE_NAME}")


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OCAC Hugo → Google Drive 反向匯出")
    parser.add_argument("--dry-run", action="store_true", help="只列出會做的事，不實際建立")
    parser.add_argument("--section", choices=SECTIONS, default=None, help="只匯出指定 section")
    parser.add_argument("--year", default=None, help="只匯出指定年份（僅 archive 有效，例如：2024）")
    args = parser.parse_args()

    if not GDRIVE_ROOT_FOLDER_ID:
        print(
            "[錯誤] 請設定環境變數 GDRIVE_ROOT_FOLDER_ID。\n"
            f"協作資料夾 ID：179KnBYYrge8Ki8HooHE7eqP2q4AayRIp"
        )
        sys.exit(1)

    service = get_drive_service() if not args.dry_run else None

    print("\n── 共用文件 ──")
    create_image_guide(service, GDRIVE_ROOT_FOLDER_ID, args.dry_run)
    create_template(service, GDRIVE_ROOT_FOLDER_ID, args.dry_run)

    sections = [args.section] if args.section else SECTIONS

    total = 0
    for section in sections:
        total += export_section(
            service,
            GDRIVE_ROOT_FOLDER_ID,
            section,
            args.year,
            args.dry_run,
        )

    print(f"\n共匯出 {total} 篇文章。")


if __name__ == "__main__":
    main()
