#!/usr/bin/env python3
"""Second pass: merge near-duplicates found via fuzzy match.

Handles:
- PETAMU (petamu-project.md + petamu-project-1.md) — same exhibition, two pages
- Close to Home (project page + 2025-日惹 page) — same screening; rescue
  bundled-but-misplaced events (Sotong) into their own stub.
"""
from pathlib import Path
import re

ZH = Path("content/zh/archive")
EN = Path("content/en/archive")


def write_md(path: Path, fm: str, body: str):
    path.write_text("---\n" + fm.strip() + "\n---\n" + body.lstrip("\n"))


def delete(*paths):
    for p in paths:
        p = Path(p) if isinstance(p, str) else p
        if p.exists():
            p.unlink()
            print(f"  deleted {p}")


# ------------------------------------------------------------------
# PETAMU merge — keep petamu-project.md (k2 alias preserved), discard -1
# ------------------------------------------------------------------
print("== PETAMU (邊境旅行) ==")
p = ZH / "petamu-project.md"
fm = """title: "邊境旅行 PETAMU Project"
date: 2018-08-30T07:01:35+08:00
draft: false
section: archive
k2_id: 427
alias: "petamu-project"
image: "/images/ui/placeholder-white.png"
tags: ["2018"]
"""
body = """
《邊境旅行 PETAMU Project》是打開—當代藝術工作站於 2018 年發起的展覽與駐地計畫。標題「PETAMU」取自馬來語、印尼語的口語用法 *Peta Kamu*（你的地圖），希望以「馬來群島」（Nusantara）的通用語（lingua franca，在此指馬來語）作為引線，打開一種觀看東南亞的另類取徑。

In the *PETAMU Project*, we use the Malay language—a *lingua franca* across Malaysia and the Indonesian archipelago—as both project name and working language. Through residency, dialogue, screening and exhibition, OCAC invites artists from Southeast Asia and Taiwan to spend a month together, re-examining the host/guest relations within Asia.

## 計畫背景

打開—當代藝術工作站與《數位荒原》駐站暨群島資料庫（Nusantara Archive）合作，整理 2016–2017 年間於印尼、馬來西亞半島的工作歷程：藝術家進駐、訪談、創作，以及與研究員／策展人合作翻譯、研究等。如同同一張地圖上各自旅行的旅人視野，匯聚為對東南亞區域的另類測繪。

「Petamu」一詞首先可理解為群島資料庫藝術家所稱的「你的地圖」——其中 *Peta* 意指地圖，*Tamu* 則可解釋為訪客。在跨國／跨文化的合作上，本計畫邀請四組藝術家與創作者透過進駐與共同合作的旅程，探索每個邊緣的複雜關係網絡，進而翻轉、開展各種偶遇與異質的連結。

## 展覽資訊

- **展期**　2018/09/01（六）— 09/30（日）
- **開幕**　2018/09/01（六）18:00
- **地點**　打開—當代藝術工作站（台北市大同區甘州街 25 號，近大橋頭站 2 號出口）
- **開放時間**　每週三–日 14:00–20:00

## 參展藝術家

- 符芳俊（馬來西亞）／曾紫詒（台灣）
- 林猷進 Jeffrey Lim（馬來西亞）／Posak Jodian（台灣）
- Syafiatudina（印尼，合作文字作者）
- 吳其育（台灣）
"""
write_md(p, fm, body)
delete(ZH / "petamu-project-1.md")

# ------------------------------------------------------------------
# Close to Home merge — keep project page; rescue 日惹 + Sotong
# ------------------------------------------------------------------
print("\n== Close to Home (project + 2025-日惹) ==")
p = ZH / "project-close-to-home-indigenous-directors.md"
fm = """title: "Close to Home — 臺灣原住民導演作品選映"
date: "2025-10-06T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/reports/2025/p015-i02-3fc61d3f93ef.jpeg"
tags: ["長期計畫", "2025"]
"""
body = """
《Close to Home》是打開—當代藝術工作站於 2025 年發起的巡映計畫，將臺灣原住民導演的影像作品帶往日惹、哥本哈根、巴黎等地，延續 *Un/Uttered 發聲與未言*（2024 大阪）以來，對亞洲原住民族影像與聲音的持續關注。計畫由 P.M.S. 策劃，打開—當代統籌；每一站不只是「放映」，更是與當地藝術社群的見面、對話與後續合作的起點。

## 各年度執行摘錄

### 2025

**日惹站｜Close to Home — 臺灣原住民導演作品選映暨臺灣之夜**

- **日期**　2025/10/06–10/07
- **地點**　Ruang MES 56，印尼日惹
- **策劃**　P.M.S.／統籌：打開—當代藝術工作站

於日惹雙年展期間，在當地具代表性的藝術空間 Ruang MES 56 舉行兩日放映。內容選映四位臺灣原住民導演的錄像作品，搭配映後座談、藝術家分享與「臺灣之夜」聚會，向日惹當地藝術團體介紹臺灣原住民影像領域的工作者與作品，並為兩地藝術社群搭建未來持續交流與互動的橋樑。

> 與本計畫並行的 2025 年其他國際巡映與駐村合作，包含哥本哈根 Art Hub Copenhagen 的「The Empowered Collective Dreaming」、亞洲藝術文獻庫「亞洲獨立藝術空間歷史與檔案」國際論壇講者參訪等，串連臺灣原住民影像與全球南方／島嶼藝術網絡。

## 圖像紀錄

![](/images/reports/2025/p015-i00-758433c258c4.jpeg)

![](/images/reports/2025/p015-i01-11a2a8a9f97d.jpeg)

![](/images/reports/2025/p015-i02-3fc61d3f93ef.jpeg)

![](/images/reports/2025/p015-i03-28a04fdefac7.jpeg)

![](/images/reports/2025/p015-i04-9c9bc63f325a.jpeg)

![](/images/reports/2025/p016-i00-97bb5bc15814.jpeg)
"""
write_md(p, fm, body)
delete(ZH / "2025-日惹放映-close-to-home-臺灣原住民導演作品選映暨臺灣之夜在日惹.md")

# ------------------------------------------------------------------
# Rescue Sotong — orphan event content from the deleted 2025-日惹 page
# (Bursting/好機/南方手勢 already have their own pages; Contingent is
#  documented inside the Bursting page; only Sotong + Sec live nowhere
#  else.)
# ------------------------------------------------------------------
print("\n== Sotong rescue ==")
p = ZH / "2025-03-Sotong-趙慈瑩作品放映會.md"
fm = """title: "開放空間放映｜《Sotong》趙慈瑩作品放映會"
date: "2025-03-01T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/ui/placeholder-white.png"
tags: ["2025"]
"""
body = """
- **日期**　2025/03/01
- **場地**　打開—當代藝術工作站

馬來西亞導演趙慈瑩（Zinc）至打開—當代進行作品放映。《Sotong》潛入馬來西亞地下變裝文化的脈動：主角 Juan，一位變裝皇后，在 2022 年吉隆坡萬聖節派對上遭警方突襲逮捕；兩年後，他與同伴們仍在地下舞台的夾縫中表演，用幽默與華麗對抗社會偏見，在表演中活出屬於自己的美麗、歡愉與痛楚。

映後座談由導演與本單位開啟，討論臺灣與馬來西亞兩地變裝文化的演變與脈絡，並進一步討論其反映的兩地文化、族群狀態。

## 導演

**趙慈瑩 Zinc**　來自馬來西亞檳城的記者與電影工作者。她偏愛真實電影（vérité）與角色驅動的敘事方式，致力於捕捉生活中的溫柔與抗爭。
"""
write_md(p, fm, body)

print("\nDone.")
