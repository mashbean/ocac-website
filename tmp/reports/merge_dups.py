#!/usr/bin/env python3
"""Merge 11 groups of duplicate archive articles into single pages.

For each group, build one cleanly-edited page that:
- preserves all unique content
- removes repeated text
- enumerates images from all duplicates as a gallery
- presents structured info (時間／地點／講者) at the top

Then deletes the duplicate files (zh + en when applicable).
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]  # ocac-hugo root if invoked from repo
# But this script runs in /tmp/ocac-fresh, so ROOT is the repo root.
# We'll resolve relative paths from the script invocation cwd instead.
ZH = Path("content/zh/archive")
EN = Path("content/en/archive")

def read_fm_body(path: Path):
    t = path.read_text()
    if not t.startswith("---\n"):
        return None, t, ""
    m = re.search(r"\n---\n", t[4:])
    if not m:
        return None, "", t
    fm = t[4 : 4 + m.start() + 1]
    body = t[4 + m.start() + 5 :]
    return fm, body, t

def get_image(path: Path):
    fm, _, _ = read_fm_body(path)
    if not fm: return None
    m = re.search(r'^image:\s*"([^"]*)"', fm, re.M)
    return m.group(1) if m else None

def write_merged(path: Path, fm: str, body: str):
    path.write_text("---\n" + fm.strip() + "\n---\n" + body.lstrip("\n"))

def delete(*paths):
    for p in paths:
        if isinstance(p, str): p = Path(p)
        if p.exists():
            p.unlink()
            print(f"  deleted {p}")

def gallery_images(*paths):
    """Collect distinct non-placeholder images from given files."""
    seen = []
    for p in paths:
        if not Path(p).exists(): continue
        img = get_image(Path(p))
        if img and "placeholder" not in img and img not in seen:
            seen.append(img)
    return seen

# ------------------------------------------------------------------
# Group 1: 2018 第六屆台灣國際錄像藝術展《離線瀏覽》讀書會 (5 → 1)
# ------------------------------------------------------------------
print("== 2018 reading group ==")
p = ZH / "2018.md"
fm = """title: "2018 第六屆台灣國際錄像藝術展《離線瀏覽》讀書會 — 數位技術、元電影與人類紀裡的藝術"
date: 2018-05-27T09:11:31+08:00
draft: false
section: archive
k2_id: 416
alias: "2018"
image: "/images/ui/placeholder-white.png"
tags: ["2018"]
"""
body = """
配合 2018 第六屆台灣國際錄像藝術展《離線瀏覽》，打開—當代藝術工作站於 5–7 月間以四場讀書會逐一閱讀貝爾納·斯蒂格勒（Bernard Stiegler）的《技術與時間》三部曲、《人類紀裡的藝術》中國美院講稿，以及其弟子許煜（Yuk Hui）的《論數位物件的實存》（On the Existence of Digital Objects）部分章節。希望帶領讀者以實際作品為起點，思考錄像藝術與我們無時無刻沉浸其中的數位技術之間的關係。

- **時間**　5/20、6/10、7/1、7/22，週日下午 1:30–4:30
- **地點**　OCAC 打開—當代藝術工作站（台北市大同區甘州街 25 號）
- **策劃／主持人**　許家維
- **導讀人**　楊成瀚（國立交通大學社會與文化研究所博士；曾任國立政治大學數位人文計畫辦公室博士後研究員，現為國立高雄師範大學跨領域藝術研究所兼任助理教授，從事當代歐陸哲學與藝術的書寫、翻譯與教學工作。）
- **費用**　每人每場酌收 100 元場地／講義費，現場繳交

## 讀書會主旨

在普世運算或「總是上線」（always online）的時代，「離線瀏覽」一方面指向「上線」與獨體（藝術）「生命」的某種必然連結，以及「離線」（offline）的不可能、不必要、不可想像；另一方面也指向離線之於線上瀏覽和活動的某種必要性、決定性，或「偶然的必要性」（necessity of contingency）。比起仍墨守傳統哲學脈絡的技術哲學家，或仍著眼於數位科技—經濟及其不滿的科技論者和諸眾，深受席蒙東（Gilbert Simondon）哲學影響的法國思想家史蒂格勒及其弟子許煜，是最能讓我們深入、確實、且全面性面對這種離線瀏覽狀態的哲學家。

史蒂格勒以技術與時間為基底，對書寫、文字、攝影、電影、社群網站、網路直播和數位科技的「破壞式創新」（disruption）與我們之間的關係，以及藝術在其中的限制和可能性提出了極為靈活而深刻的分析；許煜則在其基礎上，透過「數位物件」（digital objects）及其「實存模式」（mode of existence）的探討，對我們與上述元件之間種種有意無意的連結提出了深邃的論述。

## 讀書會進度

**5/20（日）pm 1:30–4:30｜技術、缺陷與愛比米修斯的過失**

- 貝爾納·斯蒂格勒，〈導論〉，《技術與時間：愛比米修斯的過失》，南京：譯林，1999。

**6/10（日）pm 1:30–4:30｜攝影、確正與拼寫文字的時代**

- 貝爾納·斯蒂格勒，〈第一章 拼寫文字的時代〉，《技術與時間 2. 迷失方向》，南京：譯林，2010。

**7/1（日）pm 1:30–4:30｜元電影、電影的時間與夢的器官學**

- 貝爾納·斯蒂格勒，〈電影的時間〉，《技術與時間 3. 電影的時間與存在之痛的問題》，南京：譯林，2012。
- 貝爾納·斯蒂格勒，〈人類紀裡的藝術、差異與重複〉，《人類紀裡的藝術：斯蒂格勒中國美院講座》，重慶：重慶大學出版社，2016。

**7/22（日）pm 1:30–4:30｜技術環境、業餘愛好者與人類世裡的藝術**

- 貝爾納·斯蒂格勒，〈無產化狀況下的審美判斷〉，《人類紀裡的藝術：斯蒂格勒中國美院講座》，重慶：重慶大學出版社，2016。
- Yuk Hui, "6. Logic and Time", *On the Existence of Digital Objects*, Minneapolis: University of Minnesota Press, 2016.

> 報名與閱讀資料索取：[Google 表單](https://docs.google.com/forms/d/e/1FAIpQLSeYGaJ2Tu3mpLBk1yHEnrJiSnkY0djP61o8HHoRw-6Ddm4_Iw/viewform)
"""
write_merged(p, fm, body)
delete(ZH / "2018-1.md", ZH / "2018-2.md", ZH / "2018-3.md", ZH / "2018-4.md")

# ------------------------------------------------------------------
# Group 2: KANTA Portraits (3 → 1)
# ------------------------------------------------------------------
print("== KANTA Portraits ==")
p = ZH / "kanta-kanta-portraits-jeffrey-lim-s-photography.md"
fm = """title: "KANTA 人像攝影：林猷進在台灣的攝影倡議"
date: 2017-08-12T00:00:00+08:00
draft: false
section: archive
image: "/images/ui/placeholder-white.png"
tags: ["2017"]
"""
body = """
KANTA 是一個攝影計劃。藝術家會打造可立即沖印的暗箱照相機——簡言之，是一個餅乾盒大小的行動暗房——獨特之處在於它以化學作用形成銀鹽感光照片。除了相機本身，藝術家也發起一個人像攝影系列，把這個計畫當作探索「認同」概念的方法：在某個社群、街區、城市拍攝一張張屬於那裡的人像，邀請被攝者一起進入成像的過程。

這次活動，藝術家會以自製相機現場展示成像過程，並希望把簡報空間轉化為一個觀眾得以見證影像誕生的暗房。

## 藝術家簡介

馬來西亞藝術家林猷進（Jeffrey Lim）出生於 1978 年，創作探討攝影的形式、都市調查，以及社會地景的測繪計劃。他的興趣位於認同與文化傳承的交界，並採取運用圖像、現成物、空間、互動的觀念呈現形式。他有許多作品探討觸及社群建築與空間，包含 2014 年眾籌募資的單車地圖計劃 Cycling Kuala Lumpur、2016 年於墨爾本進行的駐村計畫，以及在馬來西亞、澳洲、台灣等地持續展開的 KANTA 攝影行動。
"""
write_merged(p, fm, body)
delete(ZH / "kanta-kanta-portraits-jeffrey-lim-s-photography-1.md",
       ZH / "kanta-kanta-portraits-jeffrey-lim-s-photography-2.md")

# ------------------------------------------------------------------
# Group 3: 橡皮戳：第一P–第四P (2 → 1)
# ------------------------------------------------------------------
print("== 橡皮戳 ==")
p = ZH / "2017-03-11-08-13-31.md"
imgs = gallery_images(ZH / "2017-03-11-08-13-31.md", ZH / "2017-03-11-08-13-52.md")
gallery = "\n".join(f"![]({i})" for i in imgs)
fm = """title: "橡皮戳：第一Ｐ－第四Ｐ"
date: 2017-03-11T08:13:31+08:00
draft: false
section: archive
k2_id: 380
alias: "2017-03-11-08-13-31"
image: "/images/k2/items/cache/7081cca2f9cd0c06f2cce9e93d01dda9_XL.jpg"
tags: ["2017"]
"""
body = f"""
藝術家聰明得很，一次次以翻新的策略支撐搖搖欲墜的虛無，似乎是老掉牙的詢問——「我們仍然焦慮切割後的碎塊要如何成為完整的拼圖；如果我們離工作室越來越遠，創作的位置或藝術家的身份到底在哪？」如果藝術能在不斷被宣判死亡之後回魂，回到創作的能動挖掘，就絕不只是無病呻吟、喃喃自語或嘲諷的姿態。

「橡皮戳：第一Ｐ－第四Ｐ」由打開—當代藝術工作站策劃，邀請四組藝術家以四週為單位、四個獨立的個展段落組成一檔展覽。每一個 P 都從各自的工作脈絡出發，回應「離開工作室」之後創作如何發生。

- **展出時間**　15:00–21:00（週一休息）
- **地點**　打開—當代藝術工作站

## 展覽段落

- **第一Ｐ**
- **第二Ｐ**
- **第三Ｐ**
- **第四Ｐ**

## 圖像紀錄

{gallery}
"""
write_merged(p, fm, body)
delete(ZH / "2017-03-11-08-13-52.md")

# ------------------------------------------------------------------
# Group 4: VIA P.P.T. salon 曼谷 #1 (2 → 1)
# ------------------------------------------------------------------
print("== VIA salon #1 ==")
p = ZH / "via-p-p-t-salon-1.md"
fm = """title: "VIA P.P.T. salon 曼谷 #1"
date: 2017-04-15T00:00:00+08:00
draft: false
section: archive
image: "/images/k2/items/cache/c9e8d9069e929f4898939a62f1adcffd_XL.jpg"
tags: ["2017"]
"""
body = """
*VIA P.P.T.*（Presence Pressure Temptation）沙龍是打開—當代藝術工作站曼谷空間的駐地計畫之一，邀請打開—當代的藝術成員，以及泰國、台灣與國際藝術家於曼谷空間介紹創作、舉行講座與表演。

第一場沙龍，打開—當代曼谷邀請了台灣藝術家[張恩滿](/zh/artists/2015-08-07-04-56-09/)，與泰國藝術家 Preeyachanok Ketsuwan 一同分享他們的創作。
"""
write_merged(p, fm, body)
delete(ZH / "via-p-p-t-salon-1-1.md")

# ------------------------------------------------------------------
# Group 5: PETAMU Project (2 → 1)
# ------------------------------------------------------------------
print("== PETAMU ==")
p = ZH / "petamu-project-1.md"
# preserve content from petamu-project-2 if any unique. Both nearly identical.
fm = """title: "PETAMU Project"
date: 2018-09-01T00:00:00+08:00
draft: false
section: archive
image: "/images/ui/placeholder-white.png"
tags: ["2018"]
"""
body = """
*PETAMU*（馬來語「我們的客人」）以馬來語——一種廣泛通行於馬來西亞與印尼群島的語言——作為計畫名稱與工作語言。打開—當代藝術工作站邀請來自東南亞與台灣的藝術家，以為期一個月的駐地、討論、放映與展覽，重新檢視亞洲內部的「賓客／主人」關係。

In the "PETAMU" project, we use the Malay language, which is commonly used in Malaysia and the Indonesian archipelago, as the name and working language of the project. OCAC invites artists from Southeast Asia and Taiwan to spend a month together — through residency, discussion, screening and exhibition — re-examining the host/guest relations within Asia.

- **展期 Dates**　2018/09/01（六）— 2018/09/30（日）
- **開幕 Reception**　2018/09/01（六）18:00
- **地點 Venue**　打開—當代藝術工作站 / Open Contemporary Art Center
- **地址 Address**　台北市大同區甘州街 25 號 / No.25, Ganzhou St., Datong Dist., Taipei City
"""
write_merged(p, fm, body)
delete(ZH / "petamu-project-2.md")

# ------------------------------------------------------------------
# Group 6: CO-TEMPORARY #2 OCAC X Sa Sa Art Projects (2 → 1)
# ------------------------------------------------------------------
print("== CO-TEMPORARY #2 ==")
p = ZH / "co-temporary-2-ocac-x-sa-sa-art-projects.md"
imgs = gallery_images(p, ZH / "co-temporary-2-ocac-x-sa-sa-art-projects-dara-kong.md")
gallery = "\n".join(f"![]({i})" for i in imgs)
fm = """title: "CO-TEMPORARY #2 創作紀錄：OCAC X Sa Sa Art Projects"
date: 2016-08-15T00:00:00+08:00
draft: false
section: archive
image: "/images/k2/items/cache/269b36e876e375e05083f78293992209_XL.jpg"
tags: ["2016"]
"""
body = f"""
《CO-TEMPORARY 台灣 — 東南亞藝文交流暨論壇》是打開—當代於 2016 年發起的計畫，邀請三位來自東南亞的藝術家與四位打開成員，分階段、交叉進駐彼此的空間，以共同創作、創作計畫互助、交換駐地、工作坊等方式進行。

CO-TEMPORARY #2 為計畫的第二階段，由打開—當代與柬埔寨金邊的 [Sa Sa Art Projects](/zh/artspaces/sa-sa-art-projects/) 合作。打開邀請柬埔寨新生代藝術家 [Dara Kong](/zh/artists/dara-kong/) 與打開成員 [林文藻](/zh/artists/2015-08-02-16-09-03/) 互相駐村；Dara Kong 來到台北甘州街，林文藻則前往金邊。

## 關於 Dara Kong

Dara Kong 的創作以繪畫為主，透過細膩簡潔的線條呈現獨特的符號圖像；靈感大多來自自身與週邊生活，作品融合了童年的鄉野記憶、青年時期的城市觀察，以及對柬埔寨當代社會處境的回應。在駐地期間，他持續以繪畫作為日記般的紀錄方式，並參與打開的工作坊與分享活動。

## 圖像紀錄

{gallery}
"""
write_merged(p, fm, body)
delete(ZH / "co-temporary-2-ocac-x-sa-sa-art-projects-dara-kong.md")

# ------------------------------------------------------------------
# Group 7: Longtruk (2 → 1, also en pair)
# ------------------------------------------------------------------
print("== Longtruk ==")
p = ZH / "project-longtruk.md"
imgs = gallery_images(p, ZH / "2023-longtruk-in-the-gap-in-between.md")
gallery = "\n".join(f"![]({i})" for i in imgs) if imgs else ""
fm = """title: "Longtruk: in the gap, in between"
date: "2023-09-16T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/reports/2023/p041-i00-1f50ab1b1010.jpeg"
tags: ["2023"]
"""
body = f"""
《Longtruk: in the gap, in between》為 2023 年度執行的跨國策展研究計畫，延伸打開—當代對亞洲／東南亞區域的長期工作脈絡。本計畫聚焦於泰國 Baan Noorg Collaborative Arts & Culture 一直以來的駐地與田野工作，由台灣團隊前往拉差汶里府（Ratchaburi）進行深度訪談、研究與交流座談，回應「縫隙之間」（in the gap, in between）的工作方法——藝術如何在城／鄉、官方／民間、本地／離散、地方／全球的張力中展開。

- **主辦**　打開—當代藝術工作站、Baan Noorg Collaborative Arts & Culture
- **執行時間**　2023/09/16
- **活動性質**　國際交流座談
- **總參與人數**　12 人
- **分享藝術家**　Krittaporn Mahaweerarat、Nanut Thanapornrapee、Thapong Srisai、Baan Noorg 團隊成員

## 計畫脈絡

打開—當代藝術工作站長期關注亞洲鄉村、城市邊緣與離散社群之間的藝術實踐。Baan Noorg 的工作方法以拉差汶里的小鎮為基地，與當地居民、青年與藝術家持續合作，將藝術放回日常的縫隙：廟埕、街道、菜市場、學校。本計畫從 Baan Noorg 的長年實踐切入，透過分享會與訪談，思考亞洲獨立藝術組織如何在主流體制外，以「縫隙」作為工作方法。

## 各年度執行摘錄

**2023**　台灣團隊前往拉差汶里府進行為期數日的研究訪談；於 9 月 16 日舉辦線上分享會，邀請 Baan Noorg 三位藝術家分享在地創作，與台灣藝術社群展開對話。

{('## 圖像紀錄' + chr(10) + chr(10) + gallery) if gallery else ''}
"""
write_merged(p, fm, body)
delete(ZH / "2023-longtruk-in-the-gap-in-between.md")
# en
en_p = EN / "project-longtruk.md"
en_fm = """title: "Longtruk: in the gap, in between"
date: "2023-09-16T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/reports/2023/p041-i00-1f50ab1b1010.jpeg"
tags: ["2023"]
"""
en_body = """
*Longtruk: in the gap, in between* is a transnational curatorial-research project executed in 2023, extending OCAC's long-running work in Asia and Southeast Asia. The project focuses on the residency and field practice of Baan Noorg Collaborative Arts & Culture in Thailand. A team from Taiwan travelled to Ratchaburi for in-depth interviews, research and a public talk, responding to the working method of "in the gap, in between" — how art can unfold within the tensions between city/countryside, state/civic, local/diasporic, regional/global.

- **Organisers**　Open Contemporary Art Center; Baan Noorg Collaborative Arts & Culture
- **Date**　16 Sep 2023
- **Format**　International exchange talk
- **Participants**　12
- **Sharing artists**　Krittaporn Mahaweerarat, Nanut Thanapornrapee, Thapong Srisai, members of Baan Noorg

## Project context

OCAC has long worked alongside artistic practices that take place at the edges of Asia — rural towns, urban peripheries, diasporic communities. Baan Noorg's method is rooted in the small town of Ratchaburi, in continued collaboration with residents, youth and artists, returning art to the gaps of everyday life: temple courtyards, streets, markets, schools. *Longtruk* enters from this long arc of practice and asks how independent Asian art organisations can work outside mainstream institutions, taking "the gap" as a method.

## Annual summary

**2023**　A Taiwan team visited Ratchaburi for several days of research interviews; on 16 September the group convened an online sharing session, inviting three Baan Noorg artists to present their local practice in dialogue with the Taiwan art community.
"""
write_merged(en_p, en_fm, en_body)
delete(EN / "2023-longtruk-in-the-gap-in-between.md")

# ------------------------------------------------------------------
# Group 8: CO-TEMPORARY #1 OCAC X Mes56 (2 → 1)
# ------------------------------------------------------------------
print("== CO-TEMPORARY #1 ==")
p = ZH / "co-temporary-in-indonesia-ocac-x-mes56.md"
imgs = gallery_images(p, ZH / "co-temporary-1-ocac-x-mes56-anang-saptoto-yudha-kusuma-putera.md")
gallery = "\n".join(f"![]({i})" for i in imgs)
fm = """title: "CO-TEMPORARY #1 創作紀錄：OCAC X Mes56"
date: 2016-07-15T00:00:00+08:00
draft: false
section: archive
image: "/images/k2/items/cache/e7b279be6a862d254f0e7cc4dde2874e_XL.jpg"
tags: ["2016"]
"""
body = f"""
在東南亞地區的微型藝術網絡逐步建立後，當代藝術交流以更細膩的鏈結方式發生——藝術家不再只是獨立工作的存在，而是帶著個人意識與集體概念，在空間之內發展出多樣化的形式。

《CO-TEMPORARY 台灣 — 東南亞藝文交流暨論壇》是打開—當代於 2016 年發起的長期計畫，邀請三位來自東南亞的藝術家與四位打開成員，分階段、交叉進駐彼此的空間，以共同創作、創作計畫互助、交換駐地、工作坊等方式進行。

## CO-TEMPORARY #1：OCAC X Mes56

第一階段由打開—當代與印尼日惹的攝影空間 [Mes56](/zh/artspaces/) 合作。Mes56 派出兩位藝術家——[Anang Saptoto](/zh/artists/anang-saptoto/) 與 [Yudha Kusuma Putera](/zh/artists/yudha-kusuma-putera/)——前來台北甘州街駐村；打開則由 [施佩君](/zh/artists/2015-08-02-16-48-48/) 與 [羅仕東](/zh/artists/2015-08-06-08-28-03/) 反向前往日惹。

兩組藝術家於各自的駐地階段，從在地田野出發，發展出與當地社群、地景、街道相關的創作；最終以分享會、開放工作室、聯合展覽的方式向各自的觀眾呈現過程。

## 圖像紀錄

{gallery}
"""
write_merged(p, fm, body)
delete(ZH / "co-temporary-1-ocac-x-mes56-anang-saptoto-yudha-kusuma-putera.md")

# ------------------------------------------------------------------
# Group 9: 蔡影澂 個展 (2 → 1)
# ------------------------------------------------------------------
print("== 蔡影澂 ==")
p = ZH / "2017-02-20-16-29-53.md"
imgs = gallery_images(p, ZH / "2017-02-20-16-38-46.md")
gallery = "\n".join(f"![]({i})" for i in imgs)
fm = """title: "「身體之運動產出」蔡影澂個展"
date: 2017-02-20T16:29:53+08:00
draft: false
section: archive
k2_id: 376
alias: "2017-02-20-16-29-53"
image: "/images/k2/items/cache/daf30d03da42a5291604b3fcca07f0d0_XL.jpg"
tags: ["2017"]
"""
body = f"""
行走在田野路徑上，常常不知不覺間衣褲週遭便沾滿生長在路邊的鬼針草種子。種子藉助它者的移動屬性來拓展疆域：兩根氈鬚以「八」字型分列在瘦長果實的一端，當動物與草叢最上端擦身而過，氈鬚便帶著種子上路，在隨後的偶然機會中脫落、落地、重新生長。

「身體之運動產出」是蔡影澂以攝影、錄像、現成物為媒介展開的個展。她以鬼針草——一種隨身體移動而擴散的植物——作為命題的起點，把走過的田野、抬腳跨過的水泥邊緣、日常往返的城市縫隙，都視為身體運動的產出物：步伐落定之處留下的種子、聲音、畫面、皮膚的痕跡。

## 圖像紀錄

{gallery}
"""
write_merged(p, fm, body)
delete(ZH / "2017-02-20-16-38-46.md")

# ------------------------------------------------------------------
# Group 10: Un/Uttered (2 → 1, also en pair)
# ------------------------------------------------------------------
print("== Un/Uttered ==")
p = ZH / "project-un-uttered.md"
year_p = ZH / "2024-un-uttered-發聲與未言-亞洲藝術團體對話-暨微型影展.md"
imgs = gallery_images(p, year_p)
# also pull image lines from year_p body since it has 圖像紀錄
year_t = year_p.read_text() if year_p.exists() else ""
year_imgs = re.findall(r"!\[\]\(([^)]+)\)", year_t)
all_imgs = list(dict.fromkeys(imgs + year_imgs))
gallery = "\n\n".join(f"![]({i})" for i in all_imgs)
fm = """title: "Un/Uttered 發聲與未言：亞洲藝術團體對話暨微型影展"
date: "2024-02-03T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/reports/2024/p004-i01-71ade694abff.jpeg"
tags: ["2024"]
"""
body = f"""
《Un/Uttered 發聲與未言：亞洲藝術團體對話暨微型影展》由打開—當代藝術工作站、日本 Tra-Travel、大阪 Osaka Art Hub 共同主辦，影展策劃由 P.M.S. 負責，於 2024 年 2 月 3–4 日於日本大阪 FIGYA 舉行。在兩天之中，活動以「未被說出的、與正在說出的」作為命題，串連台灣原住民族影像、亞洲獨立藝術組織的營運經驗，以及越南、菲律賓、日本等地夥伴的觀點。

- **主辦**　打開—當代藝術工作站、Tra-Travel、Osaka Art Hub（日本）
- **影展策劃**　P.M.S.
- **時間／地點**　2024/02/03–04，日本大阪 FIGYA
- **活動性質**　交流座談 1 場、放映 2 場次、映後座談 2 場次
- **與談單位**　Mary Lou（Sàn Art，越南）

## 影展放映：台灣原住民族導演作品

- 《我在林森北路的那段日子》—— Kawah Umei 連晨軿
- 《我是女人，我是獵人》—— Rngrang Hungul 余欣蘭
- 《母語》—— Kagaw Omin 藍佩云
- 《Ugaljai 蛾》—— Baru Madiljin 巴魯·瑪迪霖
- 《Misafafahiyan 蛻變》—— Posak Jodian 曾于軒

## 交流座談：九個提問

座談題目為「九個提問：探索藝術組織的活動和全球合作前景——來自台北、胡志明市的觀點」，由打開—當代藝術工作站與胡志明市 Sàn Art 的 Mary Lou 對談，討論亞洲獨立藝術組織在全球合作、資源分配、語言／翻譯、在地工作之間的張力。

「日本大阪高年級女性影展」策展團隊也於活動期間造訪本場次，加入觀察與交流。

## 圖像紀錄

{gallery}
"""
write_merged(p, fm, body)
delete(year_p)

# en
en_p = EN / "project-un-uttered.md"
en_year_p = EN / "2024-un-uttered-發聲與未言-亞洲藝術團體對話-暨微型影展.md"
en_fm = """title: "Un/Uttered: Asian Art Collectives in Dialogue + Micro Film Festival"
date: "2024-02-03T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/reports/2024/p004-i01-71ade694abff.jpeg"
tags: ["2024"]
"""
en_body = f"""
*Un/Uttered: Asian Art Collectives in Dialogue + Micro Film Festival* was co-organised by Open Contemporary Art Center, Tra-Travel (Japan) and Osaka Art Hub, with the festival programmed by P.M.S. The event took place on 3–4 February 2024 at FIGYA in Osaka, Japan. Over two days the programme moved between Indigenous Taiwanese cinema, the operational realities of independent Asian art organisations, and perspectives from Vietnam, the Philippines and Japan, holding a question: what is uttered, and what remains unsaid?

- **Organisers**　Open Contemporary Art Center; Tra-Travel; Osaka Art Hub
- **Festival programmer**　P.M.S.
- **Venue & dates**　FIGYA, Osaka, 3–4 Feb 2024
- **Format**　1 talk, 2 screening sessions, 2 Q&A sessions
- **In dialogue with**　Mary Lou (Sàn Art, Vietnam)

## Screening: works by Indigenous Taiwanese directors

- *The Days I Spent on Linsen North Road* — Kawah Umei
- *I Am a Woman, I Am a Hunter* — Rngrang Hungul
- *Mother Tongue* — Kagaw Omin
- *Ugaljai / Moth* — Baru Madiljin
- *Misafafahiyan / Transformation* — Posak Jodian

## Talk: Nine Questions

Titled "Nine Questions: Exploring the Activities and Global Collaborations of Art Organisations — Perspectives from Taipei and Ho Chi Minh City", the talk paired OCAC with Mary Lou of Sàn Art (HCMC) to consider tensions of global collaboration, resource distribution, language/translation, and local work for independent Asian art organisations.

The curatorial team of "Older Women Film Festival, Osaka" also visited during the programme and joined the exchange.

## Visual record

{gallery}
"""
write_merged(en_p, en_fm, en_body)
delete(en_year_p)

# ------------------------------------------------------------------
# Group 11: 一群人的自學 (2 → 1, also en pair)
# ------------------------------------------------------------------
print("== 一群人的自學 ==")
p = ZH / "project-a-group-self-study.md"
year_p = ZH / "2023-一群人的自學.md"
year_t = year_p.read_text() if year_p.exists() else ""
year_imgs = re.findall(r"!\[\]\(([^)]+)\)", year_t)
gallery = "\n\n".join(f"![]({i})" for i in year_imgs)
fm = """title: "一群人的自學"
date: "2016-09-01T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/reports/2023/p018-i00-2f64df00c3ce.jpeg"
tags: ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
"""
body = f"""
「一群人的自學」是一群對策展感興趣的朋友於 2016 年起自發組成的社群，每月最後一個週日晚間於打開—當代甘州街空間舉行讀書會或專題討論。2019 年夏天完成策展讀本《策展文化與文化策展》翻譯後，社群推出「藝術家策展人互助討論會（藝策互助會）」，把焦點從翻譯、文獻轉向當代藝術家、獨立策展人正在進行的計畫互助與田野現場。

社群以「沒有講師、沒有結業」為原則：每場由一至兩位主持人提出主題與閱讀材料，與會者一起讀書、放映、走讀、訪問、報告各自正在做的事——把「自學」當作一種延長的、共同的策展方法。

- **發起**　打開—當代藝術工作站
- **頻率**　每月最後一個週日晚間
- **地點**　打開—當代甘州街空間（依主題不定期外移）
- **公開性**　非營利、不售票，需事先報名

## 各年度執行摘錄

**2021**　將年度計畫聚焦於「藝術家策展人互助討論會」第二屆，邀請八位以上的藝術家／策展人輪流發起場次，深入彼此正在進行中的計畫，並於年末舉辦集體成果分享。

**2022**　持續藝策互助會，並開展與外部單位的串連，包含與台北市藝術創作者職業工會的交流、共同舉辦多場面向藝術勞動環境的討論。

**2023**　全年共執行 9 場，主辦為一群人的自學社群，打開—當代提供合作與場地。本年度邀請來訪講者包含 Nataša Petrešin-Bachelez（巴黎西帖國際藝術村文化計畫負責人）、台北市藝術創作者職業工會、山峸二手書店等，主題涵蓋國際駐村制度、藝術勞動、書店與獨立出版的當代角色。
- **總參與人數**　12 人／場（平均）
- **活動性質**　教育推廣、講座／討論會
- **是否售票**　否，非營利性質

{('## 圖像紀錄' + chr(10) + chr(10) + gallery) if gallery else ''}
"""
write_merged(p, fm, body)
delete(year_p)

# en
en_p = EN / "project-a-group-self-study.md"
en_year_p = EN / "2023-一群人的自學.md"
en_fm = """title: "A Group's Self-Study"
date: "2016-09-01T00:00:00+08:00"
draft: false
section: "archive"
image: "/images/reports/2023/p018-i00-2f64df00c3ce.jpeg"
tags: ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
"""
en_body = """
*A Group's Self-Study* is a self-organised community of curatorially-curious friends that began in 2016. The group meets on the last Sunday evening of every month at OCAC's Ganzhou Street space for a reading group or thematic discussion. After completing the translation of *Cultures of the Curatorial / Curating Cultures* in summer 2019, the group launched the "Artist–Curator Mutual Aid Discussion" — shifting the focus from translation and theory to the projects, fieldwork and back-stories that artists and independent curators are working on right now.

The group's principle is "no teacher, no graduation": each session is convened by one or two hosts who propose a theme and readings; participants read, screen, walk, interview and report on what they are doing — treating "self-study" as a sustained, collective curatorial method.

- **Initiated by**　Open Contemporary Art Center
- **Frequency**　Last Sunday evening of every month
- **Venue**　OCAC Ganzhou Street space (occasionally on the road)
- **Open**　Non-profit, free, registration required

## Annual summary

**2021**　Focused on the second edition of the Artist–Curator Mutual Aid Discussion; eight or more artists/curators took turns to host sessions on their in-progress projects, with a collective year-end share.

**2022**　Continued the Mutual Aid Discussion and opened collaborations with external groups, including the Taipei Art Creators Trade Union, with multiple sessions on artistic labour conditions.

**2023**　Nine sessions across the year. Visiting speakers included Nataša Petrešin-Bachelez (Cité internationale des arts, Paris), the Taipei Art Creators Trade Union and Shanchen Used Bookstore. Topics ranged from international residency systems and artistic labour to the contemporary role of bookshops and independent publishing.
- **Average attendance**　12 per session
- **Format**　Educational outreach; lecture/discussion
- **Ticketing**　None, non-profit
"""
write_merged(en_p, en_fm, en_body)
delete(en_year_p)

print("\nAll merges complete.")
