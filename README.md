# OCAC 打開—當代藝術工作站 網站

> [ocac.tw](https://ocac.tw) — Open Contemporary Art Center, Tainan / Taipei, Taiwan

中英雙語靜態網站，以 [Hugo](https://gohugo.io) 生成，部署於 Cloudflare Pages。
內容自原 Joomla/K2 網站遷移，並補齊 2020–2025 年度結案報告的活動紀錄。

---

## 技術棧

| 項目 | 工具 |
|------|------|
| 靜態產生器 | Hugo `0.147.0` |
| 主機 | Cloudflare Pages（自動建構） |
| 網域 | ocac.tw |
| 版本控管 | GitHub `mashbean/ocac-website` |
| 內容語言 | `content/zh/`（繁中主站）、`content/en/` |

---

## 目錄結構

```
ocac-hugo/
├── hugo.toml              # 網站設定（標題、選單、雙語）
├── content/
│   ├── zh/                # 中文主站
│   │   ├── archive/       # 年度計畫 + 活動紀錄
│   │   ├── artists/       # 藝術家列表頁
│   │   ├── artspaces/     # 合作藝術空間
│   │   ├── about/         # 關於
│   │   ├── visit/         # 參觀資訊
│   │   └── contact/       # 聯絡
│   └── en/                # 英文鏡像（結構同上）
├── layouts/               # HTML template
│   ├── _default/          # list、single、baseof
│   ├── partials/          # header、footer、語言切換
│   └── index.html
├── static/
│   ├── css/main.css       # 設計系統 v2.1
│   ├── js/main.js
│   └── images/            # K2 舊圖 + 年度報告圖片
└── tmp/reports/           # 年度報告內容處理腳本（離線工具，詳見下方）
```

詳細部署步驟見 [`DEPLOY.md`](DEPLOY.md)。

---

## 內容 pipeline

### 既有內容（K2 遷移）

老網站的 Joomla/K2 資料以 SQL dump 匯出，再以腳本轉成 Hugo markdown。
舊文件 slug 保留在 frontmatter 的 `k2_id` 與 `alias` 欄位，方便日後重定向。

### 2020–2025 年度報告（2026 補齊）

從 `~/Downloads/2019-2025 打開結案報告/` 的 PDF／.doc 原始檔提取文字與圖片，
三階段生成 archive 文章：

1. **Phase 1** — 年度回顧 `report-{year}.md`（12 檔，zh+en）
2. **Phase 2** — 長期計畫專頁 `project-{slug}.md`（24 檔）
3. **Phase 3** — 個別活動紀錄 `{year}-{slug}.md`（89 檔活動頁）

處理腳本均在 `tmp/reports/`，可重跑以擴充或修正：

| 腳本 | 用途 |
|------|------|
| `extract.py` | PyMuPDF 原生圖片＋文字提取 |
| `generate.py` | 三階段 markdown 生成 |
| `fix_2020.py` | 2020 簡報式時間軸特化解析 |
| `clean_cjk.py` | 康熙部首偽字修正（⾺ → 馬 等） |
| `fix_frontmatter.py` | 多行 YAML 標題收合 |
| `cleanup.py` | 去除封面樣板、依標題去重、PDF 斷行修復 |
| `gen_entities.py` | 由文章提及生成藝術家／藝術空間條目 |

> 年度報告圖片共 357 張約 30MB，位於 `static/images/reports/{year}/`。
> 文字內容仍屬「先上線再校正」狀態，frontmatter 皆附 `*本文由結案報告整理，內容待後續補齊*` 註記。

### 新增內容

在 `content/{zh,en}/{section}/` 建立 markdown，frontmatter 需有 `title`、`date`、`draft: false`、`section`。
push 到 `main` 後 Cloudflare Pages 會在數十秒內重建。

---

## 本地預覽

```bash
brew install hugo          # macOS
cd ocac-hugo
hugo server -D             # http://localhost:1313
```

---

## 分支策略

- `main` — 唯一正式分支，push 即部署
- 不使用 feature branch；大改動直接 commit，Cloudflare Pages 保留歷史預覽

---

## 授權

內容 © Open Contemporary Art Center。網站程式碼 MIT（見 `LICENSE` — 若尚未新增請向維護者索取）。
