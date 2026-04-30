# OCAC 網站 — Claude Code 操作指南

> 本站為 Hugo 靜態網站，部署於 Cloudflare Pages，原始碼位於 GitHub `mashbean/ocac-website`。
> push 到 `main` 後 Cloudflare 會在數十秒內自動重建部署。

---

## 目錄

1. [專案結構](#專案結構)
2. [Hugo Front Matter 規格](#hugo-front-matter-規格)
3. [Google Drive 協作流程](#google-drive-協作流程)
4. [一鍵同步指令](#一鍵同步指令)
5. [Google Drive 資料夾結構](#google-drive-資料夾結構)
6. [同步腳本邏輯](#同步腳本邏輯)
7. [首次設定](#首次設定)
8. [常見操作](#常見操作)

---

## 專案結構

```
ocac-website/
├── content/
│   ├── zh/                  # 中文主站
│   │   ├── archive/         # 年度活動紀錄
│   │   ├── artists/         # 藝術家
│   │   └── artspaces/       # 合作藝術空間
│   └── en/                  # 英文鏡像
├── static/
│   └── images/
│       └── gdrive/          # Google Drive 同步下來的圖片（自動管理）
├── gdrive-templates/        # 提供給同事的 Markdown 模板
│   ├── archive-template.md
│   ├── artists-template.md
│   └── artspaces-template.md
└── scripts/
    ├── gdrive_sync.py       # 一鍵同步腳本
    ├── gdrive_auth.py       # 首次 OAuth2 授權
    └── requirements.txt
```

---

## Hugo Front Matter 規格

### archive（活動紀錄）

```yaml
---
title: "活動名稱"
date: "2025-01-01T00:00:00+08:00"   # 活動開始日期（必填）
endDate: "2025-01-03T00:00:00+08:00" # 活動結束日期（有跨日才填）
draft: false
section: "archive"
image: "/images/gdrive/zh/archive/slug/cover.jpg"  # 封面圖（選填）
tags: ["2025"]                        # 年份 tag（必填）
sources: ["facebook-events"]          # 來源（選填）
---
```

### artists（藝術家）

```yaml
---
title: "藝術家姓名"
date: "2025-01-01T00:00:00+08:00"
draft: false
section: "artists"
alias: "artist-name-slug"   # URL slug，英文小寫連字號
image: "/images/gdrive/zh/artists/slug/portrait.jpg"
nationality: "Taiwan"        # 國籍（選填）
---
```

### artspaces（藝術空間）

```yaml
---
title: "空間名稱"
date: "2025-01-01T00:00:00+08:00"
draft: false
section: "artspaces"
alias: "space-name-slug"
image: "/images/gdrive/zh/artspaces/slug/cover.jpg"
country: "Indonesia"   # 國家（選填）
city: "Yogyakarta"     # 城市（選填）
---
```

---

## Google Drive 協作流程

同事只需要在 Google Drive 做三件事：

1. 在對應的語言／section 資料夾下新增一個**文章資料夾**（名稱即為文章 slug）
2. 在資料夾內放一個 `content.md`（依模板撰寫）
3. 若有圖片，建立 `images/` 子資料夾並上傳圖片

完成後通知負責人執行同步指令即可。

### Google Drive 資料夾命名規則

- 資料夾名稱會直接作為 Hugo slug（URL 路徑）
- 使用英文小寫 + 數字 + 連字號，例如：`2025-terap-festival-sharing`
- 中文字可保留，腳本會自動處理（例如：`2025-相遇何處-萬隆分享記`）
- 檔名必須是 `content.md`（大小寫不分）

---

## 一鍵同步指令

```bash
# 同步全部內容（zh + en，全部 section）
python scripts/gdrive_sync.py

# 預覽模式（不實際寫入，只列出會做什麼）
python scripts/gdrive_sync.py --dry-run

# 只同步某個 section
python scripts/gdrive_sync.py --section archive

# 只同步中文
python scripts/gdrive_sync.py --lang zh

# 組合使用
python scripts/gdrive_sync.py --lang zh --section archive --dry-run
```

同步成功後腳本會自動：
1. 將 Markdown 寫入 `content/` 對應路徑
2. 將圖片下載到 `static/images/gdrive/`
3. `git add` → `git commit` → `git push origin main`
4. Cloudflare Pages 收到 push 後自動部署（約 30–60 秒）

---

## Google Drive 資料夾結構

```
OCAC-Website-Content/                ← 根資料夾（ID 填入環境變數）
├── zh/
│   ├── archive/
│   │   └── 2025-terap-festival/    ← 文章資料夾（名稱 = slug）
│   │       ├── content.md          ← 必要
│   │       └── images/             ← 選填
│   │           ├── cover.jpg
│   │           └── photo-01.jpg
│   ├── artists/
│   │   └── chen-chieh-jen/
│   │       ├── content.md
│   │       └── images/
│   └── artspaces/
│       └── nha-san-collective/
│           ├── content.md
│           └── images/
└── en/
    ├── archive/
    ├── artists/
    └── artspaces/
```

---

## 同步腳本邏輯

`scripts/gdrive_sync.py` 的處理流程：

1. **授權**：讀取 `scripts/gdrive_token.json`（首次執行需先跑 `gdrive_auth.py`）
2. **遍歷**：依 `lang → section → 文章資料夾` 三層結構遍歷 Drive
3. **下載**：取得 `content.md` 並下載所有 `images/` 內的圖片
4. **處理**：若 front matter `image` 欄位為空，自動填入第一張圖片的路徑
5. **比對**：只有當 Markdown 內容有變更，或圖片是新的，才計入 changed
6. **部署**：有任何變更就 `git add → commit → push`，觸發 Cloudflare 部署

---

## 首次設定

### 1. 安裝 Python 依賴

```bash
pip install -r scripts/requirements.txt
```

### 2. 建立 Google Cloud 專案並啟用 API

1. 前往 https://console.cloud.google.com/
2. 建立新專案（例如：`ocac-website-sync`）
3. 左側選單 → **API 和服務** → **啟用 API**
4. 搜尋並啟用 **Google Drive API**
5. 左側 → **憑證** → **建立憑證** → **OAuth 2.0 用戶端 ID**
6. 應用程式類型選「**桌面應用程式**」
7. 下載 JSON，重新命名為 `gdrive_credentials.json`
8. 放到 `scripts/` 資料夾

### 3. 首次授權

```bash
python scripts/gdrive_auth.py
```

瀏覽器會開啟 Google 授權頁面，登入並授權後 token 會儲存到 `scripts/gdrive_token.json`。

### 4. 設定 Google Drive 根資料夾 ID

在 Google Drive 中建立根資料夾（例如命名 `OCAC-Website-Content`），
打開該資料夾，複製 URL 中 `/folders/` 後的 ID，設定環境變數：

```bash
export GDRIVE_ROOT_FOLDER_ID="1aBcDeFgHiJkLmNoPqRsTuVwXyZ"
```

或直接編輯 `scripts/gdrive_sync.py` 頂部的 `GDRIVE_ROOT_FOLDER_ID` 變數。

建議加入 shell 設定檔（`~/.zshrc` 或 `~/.bashrc`）：
```bash
echo 'export GDRIVE_ROOT_FOLDER_ID="你的資料夾ID"' >> ~/.zshrc
```

### 5. 將 token 和 credentials 加入 .gitignore

確認 `.gitignore` 包含以下（避免憑證上傳到 GitHub）：

```
scripts/gdrive_credentials.json
scripts/gdrive_token.json
```

---

## 常見操作

### 手動新增一篇文章（不經 Drive）

```bash
# 在對應路徑直接建立 md 檔
# 格式參考 gdrive-templates/ 內的模板
vim content/zh/archive/2025-new-event.md
git add content/zh/archive/2025-new-event.md
git commit -m "add: 2025 新活動"
git push
```

### 本地預覽

```bash
hugo server -D   # http://localhost:1313
```

### 只更新圖片

圖片放到 `static/images/` 對應資料夾後直接 commit push：

```bash
git add static/images/
git commit -m "add: 新增活動圖片"
git push
```

### 查看部署狀態

Cloudflare Pages Dashboard → Workers & Pages → ocac-website → Deployments
