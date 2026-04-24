#!/usr/bin/env python3
"""Generate artist + art-space content entries from archive article mentions.

Approach:
- Curated seed list (bilingual) of artists and art spaces seen across the
  2020–2025 annual report PDFs.
- Cross-check against existing content/{zh,en}/{artists,artspaces}/ titles
  (NFKC-normalised).
- For missing entries, verify the name actually appears in at least one
  archive article body — skip otherwise.
- Emit markdown stubs matching the existing schema, with a one-sentence
  placeholder bio/description (to be refined manually).
"""
from pathlib import Path
import re, unicodedata, datetime

ROOT = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo")
CONTENT = ROOT / "content"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", "", s)
    return s.lower()


def load_existing(section: str, lang: str):
    base = CONTENT / lang / section
    titles = set()
    for f in base.iterdir():
        if not f.is_file() or f.name == "_index.md":
            continue
        t = f.read_text()
        m = re.search(r'^title:\s*[\"\']?([^\"\'\n]+?)[\"\']?\s*$', t, re.M)
        if m:
            titles.add(norm(m.group(1)))
    return titles


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    # Keep ASCII letters/digits; replace rest with -
    s = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "-", s).strip("-").lower()
    return s or "untitled"


# ---------- Curated bilingual seed list ----------
# Each entry: key (zh primary), en title, description_zh, description_en, year first seen
ARTISTS = [
    # name_zh, name_en, bio_zh, bio_en, year
    ("Posak Jodian 曾于軒", "Posak Jodian",
     "阿美族影像工作者，創作關注部落記憶、女性身體與離散經驗。近年與打開-當代藝術工作站合作，於台北雙年展、台東、蘭嶼等地進行影像田野與放映。",
     "Amis filmmaker whose work traces tribal memory, women's bodies and diasporic experience. Recently collaborated with OCAC on fieldwork and screenings across Taipei, Taitung and Orchid Island.",
     "2023"),
    ("Kawah Umei 連晨軿", "Kawah Umei",
     "泰雅族導演，作品《我在林森北路的那段日子》以自身經驗書寫都市原住民的生活切面。",
     "Atayal director whose film 〈The Days I Spent on Linsen North Road〉 documents urban Indigenous life from lived experience.",
     "2024"),
    ("Rngrang Hungul 余欣蘭", "Rngrang Hungul",
     "泰雅族導演。作品《我是女人，我是獵人》穿梭於部落狩獵文化與性別敘事之間。",
     "Atayal director. Her film 〈I Am a Woman, I Am a Hunter〉 moves between tribal hunting culture and gendered narrative.",
     "2024"),
    ("Kagaw Omin 藍佩云", "Kagaw Omin",
     "阿美族導演，短片《母語》描繪語言傳承與家族日常。",
     "Amis director; her short 〈Mother Tongue〉 portrays language transmission and family life.",
     "2024"),
    ("Baru Madiljin 巴魯・瑪迪霖", "Baru Madiljin",
     "排灣族導演，作品《Ugaljai 蛾》結合神話與土地影像。",
     "Paiwan director; 〈Ugaljai / Moth〉 weaves myth with the landscape.",
     "2024"),
    ("Jane Jin Kaisen", "Jane Jin Kaisen",
     "韓裔丹麥藝術家，生於濟州島，工作於哥本哈根。以錄像裝置、電影、攝影、文字書寫與跨界研究探索遷移、邊界、轉譯與集體記憶。曾代表韓國參加第 58 屆威尼斯雙年展。",
     "Korean–Danish artist, born on Jeju Island, based in Copenhagen. Works across video installation, film, photography, performance and text; her practice explores migration, borders, translation and collective memory. Represented Korea at the 58th Venice Biennale.",
     "2023"),
    ("Anselm Franke 安森・法蘭克", "Anselm Franke",
     "1978 年生，2012 年策劃台北雙年展「現代怪獸／想像的死而復生」。2013–2022 年任柏林世界文化宮（HKW）視覺藝術與影像部總監。現為蘇黎世藝術大學策展研究教授。",
     "Born 1978. Curated the 2012 Taipei Biennial, 'Modern Monsters / Death and Life of Fiction'. Head of Visual Arts and Film at Berlin's Haus der Kulturen der Welt (HKW) 2013–2022. Currently Professor of Curatorial Studies at Zurich University of the Arts.",
     "2023"),
    ("Mary Lou Pangilinan-Domingo", "Mary Lou Pangilinan-Domingo",
     "菲律賓／越南藝術工作者，Sàn Art 團隊成員，關注東南亞當代藝術組織間的合作與知識生產。",
     "Filipino-Vietnamese arts worker, member of Sàn Art, focused on collaboration and knowledge production among Southeast Asian art organisations.",
     "2024"),
    ("許雁婷", "HSU Yen-Ting",
     "聲音藝術家與紀錄片工作者，作品橫跨聲音採集、現場演出與跨領域合作。曾參與台北雙年展「一隻蒼蠅飛入海洋無垠的吐納」演出。",
     "Sound artist and documentary maker whose work spans field recording, live performance and cross-disciplinary collaboration. Performed at the 2024 Taipei Biennial programme.",
     "2024"),
    ("莊勝凱", "CHUANG Sheng-Kai",
     "聲響創作者，長期參與失聲祭與打開-當代藝術工作站之現場演出與錄音計畫。",
     "Sound practitioner, a long-time collaborator in Lacking Sound Festival and OCAC live-performance programmes.",
     "2024"),
    ("巴奈・庫穗", "Panai Kusui",
     "卑南／阿美族音樂人，以歌聲與社會運動並行，作品回應土地正義、原住民族權利等議題。",
     "Puyuma/Amis musician whose singing walks alongside social movement; her work responds to land justice and Indigenous rights.",
     "2024"),
    ("賴宗昀", "LAI Tsung-Yun",
     "聲音／影像藝術家，創作遊走於電子聲響、表演與裝置之間。",
     "Sound and moving-image artist working across electronic sound, performance and installation.",
     "2024"),
    ("黃大旺", "HUANG Da-Wang",
     "聲音藝術家與譯者，以即興、口述與日常語音重構聆聽的邊界。",
     "Sound artist and translator whose practice of improvisation, oral narration and everyday voice remaps the edges of listening.",
     "2024"),
    ("Sundialll", "Sundialll",
     "電子音樂創作者，跨足實驗電子、環境聲響與表演。",
     "Electronic music producer working across experimental electronics, ambient sound and live performance.",
     "2024"),
    ("Arief Budiman", "Arief Budiman",
     "印尼導演，與 Bonny Lanny、Harun Rumbarar 共同執導紀錄片《我們的 Wisisi 之歌》。",
     "Indonesian filmmaker who co-directed the documentary 〈Our Song of Wisisi〉 with Bonny Lanny and Harun Rumbarar.",
     "2024"),
    ("Bonny Lanny", "Bonny Lanny",
     "印尼導演，與 Arief Budiman、Harun Rumbarar 共同執導《我們的 Wisisi 之歌》。",
     "Indonesian filmmaker who co-directed 〈Our Song of Wisisi〉 with Arief Budiman and Harun Rumbarar.",
     "2024"),
    ("Harun Rumbarar", "Harun Rumbarar",
     "印尼導演，與 Arief Budiman、Bonny Lanny 共同執導《我們的 Wisisi 之歌》。",
     "Indonesian filmmaker who co-directed 〈Our Song of Wisisi〉 with Arief Budiman and Bonny Lanny.",
     "2024"),
    ("朱利安・亞伯拉罕「多加」", "Julian 'Togar' Abraham",
     "印尼跨領域藝術家，音樂、科學研究與社群實踐是其創作的主要語彙。",
     "Indonesian interdisciplinary artist whose vocabulary spans music, scientific research and community practice.",
     "2024"),
    ("Mirwan Andan", "Mirwan Andan",
     "印尼 ruangrupa 團體成員，關注集體創作、資源共享與當代藝術組織。",
     "Member of Indonesian collective ruangrupa; focused on collective practice, resource sharing and contemporary art organisations.",
     "2022"),
    ("柯念璞", "KO Nien-Pu",
     "策展人與研究者，策劃原住民當代藝術與跨國田野計畫。",
     "Curator and researcher working on Indigenous contemporary art and transnational fieldwork.",
     "2023"),
    ("徐詩雨", "HSU Shih-Yu",
     "策展人、寫作者，關注影像、檔案與記憶政治。",
     "Curator and writer focused on moving image, archive and the politics of memory.",
     "2023"),
]

ARTSPACES = [
    # name_zh, name_en, desc_zh, desc_en, country
    ("Á Space", "Á Space",
     "位於越南河內的獨立藝術空間，支持東南亞的跨域研究、駐村與展演。",
     "An independent art space in Hanoi, Vietnam, supporting cross-disciplinary research, residency and performance across Southeast Asia.",
     "Vietnam"),
    ("Nha San Collective", "Nha San Collective",
     "越南河內老牌實驗藝術社群，是東南亞獨立藝術生態的重要節點。",
     "A long-running experimental art community in Hanoi, Vietnam; a key node in the Southeast Asian independent art ecology.",
     "Vietnam"),
    ("ba-bau AIR", "ba-bau AIR",
     "越南河內駐村空間，專注於跨國藝術家的研究、駐村與發表。",
     "A residency space in Hanoi, Vietnam, dedicated to transnational artist research, residency and presentation.",
     "Vietnam"),
    ("Sàn Art", "Sàn Art",
     "越南胡志明市具代表性的獨立當代藝術組織，長期推動東南亞當代藝術的策展、駐村與教育計畫。",
     "A leading independent contemporary art organisation based in Ho Chi Minh City, Vietnam, with long-standing programmes in curation, residency and education across Southeast Asia.",
     "Vietnam"),
    ("Jatiwangi Art Factory", "Jatiwangi Art Factory",
     "印尼西爪哇的鄉村藝術組織，以陶土、聲響與土地為創作媒介，關注村落與全球化之間的張力。",
     "A rural art organisation in West Java, Indonesia, working with clay, sound and the land to examine the tensions between village life and globalisation.",
     "Indonesia"),
    ("Osaka Art Hub", "Osaka Art Hub",
     "日本大阪的藝術組織，促進亞洲藝術社群間的交流與合作。",
     "An arts organisation in Osaka, Japan, fostering exchange and collaboration among Asian art communities.",
     "Japan"),
    ("FIGYA", "FIGYA",
     "日本大阪的獨立藝術空間，長期主辦實驗音樂、影像放映與跨領域活動。",
     "An independent art space in Osaka, Japan, regularly hosting experimental music, screenings and cross-disciplinary events.",
     "Japan"),
    ("Tra-Travel", "Tra-Travel",
     "日本獨立策展／交流計畫，促進亞洲藝術組織間的互訪與合作。",
     "An independent Japan-based curatorial and exchange initiative that facilitates mutual visits and collaboration among Asian art organisations.",
     "Japan"),
    ("P.M.S.", "P.M.S.",
     "以影像放映、策劃與微型影展為核心的工作團隊，關注當代影像文化。",
     "A working group focused on screenings, programming and micro-festivals dedicated to contemporary moving-image culture.",
     "Taiwan"),
    ("Mekong Cultural Hub", "Mekong Cultural Hub",
     "跨越湄公河流域的文化網絡，支持東南亞藝術工作者的串連、研究與實踐。",
     "A cultural network spanning the Mekong region, supporting networking, research and practice among Southeast Asian arts workers.",
     "Regional / Southeast Asia"),
    ("SAVVY Contemporary", "SAVVY Contemporary",
     "位於柏林的獨立藝術機構，著力於去殖民、跨域與全球南方的論述生產。",
     "An independent art institution in Berlin committed to decolonial, cross-disciplinary practice and Global South discourse.",
     "Germany"),
    ("Asia Art Archive", "Asia Art Archive",
     "香港非營利組織，建置亞洲當代藝術檔案與研究基礎設施。",
     "A Hong Kong–based non-profit building archival and research infrastructure for contemporary art in Asia.",
     "Hong Kong"),
    ("Azul Arena", "Azul Arena",
     "來自菲律賓的藝術組織，關注當代表演、社群組織與跨文化計畫。",
     "A Philippines-based arts organisation focused on contemporary performance, community organising and cross-cultural projects.",
     "Philippines"),
    ("LIR Space", "LIR Space",
     "印尼日惹的藝術空間，關注出版、書籍與在地社群的串連。",
     "An art space in Yogyakarta, Indonesia, focused on publishing, books and community networks.",
     "Indonesia"),
    ("matca", "matca",
     "越南河內的攝影空間與社群，支援當代攝影的實驗、教育與出版。",
     "A photography space and community in Hanoi, Vietnam, supporting experimental, educational and publishing work in contemporary photography.",
     "Vietnam"),
    ("COAC", "COAC",
     "菲律賓獨立藝術組織，推動當代藝術的實驗、策展與跨域合作。",
     "A Philippines-based independent arts organisation advancing contemporary art experimentation, curation and cross-disciplinary collaboration.",
     "Philippines"),
    ("Art Hub Copenhagen", "Art Hub Copenhagen",
     "丹麥哥本哈根的藝術支持組織，提供研究、駐村與發展計畫給國際藝術家。",
     "A Copenhagen, Denmark art-support organisation offering research, residency and development programmes to international artists.",
     "Denmark"),
    ("失聲祭", "Lacking Sound Festival",
     "台灣長期推動實驗聲音與現場演出的平台，與打開-當代藝術工作站多次合作。",
     "A long-running Taiwanese platform for experimental sound and live performance, with multiple collaborations with OCAC.",
     "Taiwan"),
    ("立方計畫空間", "TheCube Project Space",
     "位於台北的獨立藝術機構，長期經營當代藝術、聲響與檔案研究。",
     "An independent art institution in Taipei with sustained work in contemporary art, sound and archival research.",
     "Taiwan"),
    ("鳳甲美術館", "Hong-Gah Museum",
     "台灣台北市北投的美術館，曾主辦 Jane Jin Kaisen 來台駐訪與田野研究計畫。",
     "A museum in Beitou, Taipei, Taiwan, which hosted Jane Jin Kaisen's visit and fieldwork research in Taiwan.",
     "Taiwan"),
    ("台北市立美術館", "Taipei Fine Arts Museum",
     "台灣台北的公立美術館，長期主辦台北雙年展等重要當代藝術計畫。",
     "A public art museum in Taipei, Taiwan, and home to the Taipei Biennial and other major contemporary art programmes.",
     "Taiwan"),
]


# ---------- Emit markdown ----------
TODAY = "2025-12-31T00:00:00+08:00"


def body_for_artist(d_zh: str):
    return d_zh + "\n"


def emit_artist(name_zh: str, name_en: str, bio_zh: str, bio_en: str, year: str, existing_zh: set, existing_en: set):
    written = 0
    # zh
    if norm(name_zh) not in existing_zh:
        slug = slugify(name_en)  # use english slug for url cleanness
        path = CONTENT / "zh" / "artists" / f"{slug}.md"
        if path.exists():
            path = CONTENT / "zh" / "artists" / f"{slug}-{year}.md"
        fm = (f"---\n"
              f"title: \"{name_zh}\"\n"
              f"date: {TODAY}\n"
              f"draft: false\n"
              f"section: artists\n"
              f"tags: [\"{year}\"]\n"
              f"---\n")
        path.write_text(fm + bio_zh + "\n\n---\n\n*條目自 2020–2025 打開-當代藝術工作站結案報告整理，簡介待後續補齊。*\n")
        written += 1
    # en
    if norm(name_en) not in existing_en:
        slug = slugify(name_en)
        path = CONTENT / "en" / "artists" / f"{slug}.md"
        if path.exists():
            path = CONTENT / "en" / "artists" / f"{slug}-{year}.md"
        fm = (f"---\n"
              f"title: \"{name_en}\"\n"
              f"date: {TODAY}\n"
              f"draft: false\n"
              f"section: artists\n"
              f"tags: [\"{year}\"]\n"
              f"---\n")
        path.write_text(fm + bio_en + "\n\n---\n\n*Compiled from OCAC 2020–2025 annual closing reports; full biography to be added.*\n")
        written += 1
    return written


def emit_artspace(name_zh: str, name_en: str, desc_zh: str, desc_en: str, country: str, existing_zh: set, existing_en: set):
    written = 0
    if norm(name_zh) not in existing_zh:
        slug = slugify(name_en)
        path = CONTENT / "zh" / "artspaces" / f"{slug}.md"
        fm = (f"---\n"
              f"title: \"{name_zh}\"\n"
              f"date: {TODAY}\n"
              f"draft: false\n"
              f"section: artspaces\n"
              f"country: \"{country}\"\n"
              f"---\n")
        path.write_text(fm + desc_zh + "\n\n---\n\n*條目自 2020–2025 打開-當代藝術工作站結案報告整理，介紹待後續補齊。*\n")
        written += 1
    if norm(name_en) not in existing_en:
        slug = slugify(name_en)
        path = CONTENT / "en" / "artspaces" / f"{slug}.md"
        fm = (f"---\n"
              f"title: \"{name_en}\"\n"
              f"date: {TODAY}\n"
              f"draft: false\n"
              f"section: artspaces\n"
              f"country: \"{country}\"\n"
              f"---\n")
        path.write_text(fm + desc_en + "\n\n---\n\n*Compiled from OCAC 2020–2025 annual closing reports; description to be refined.*\n")
        written += 1
    return written


def main():
    existing_artists_zh = load_existing("artists", "zh")
    existing_artists_en = load_existing("artists", "en")
    existing_spaces_zh = load_existing("artspaces", "zh")
    existing_spaces_en = load_existing("artspaces", "en")

    # Gather corpus of archive article text for verification
    corpus = ""
    for lang in ("zh", "en"):
        for p in (CONTENT / lang / "archive").iterdir():
            if p.is_file():
                corpus += p.read_text() + "\n"
    corpus_norm = norm(corpus)

    new_artists = 0
    skipped_artists = 0
    for name_zh, name_en, bio_zh, bio_en, year in ARTISTS:
        # verify one of the names actually appears in corpus
        if norm(name_zh.split(" ")[0]) not in corpus_norm and norm(name_en) not in corpus_norm:
            # Also try the first Chinese token (before space)
            zh_token = name_zh.split(" ")[-1]
            if norm(zh_token) not in corpus_norm:
                skipped_artists += 1
                continue
        new_artists += emit_artist(name_zh, name_en, bio_zh, bio_en, year,
                                   existing_artists_zh, existing_artists_en)

    new_spaces = 0
    skipped_spaces = 0
    for name_zh, name_en, desc_zh, desc_en, country in ARTSPACES:
        if norm(name_zh) not in corpus_norm and norm(name_en) not in corpus_norm:
            skipped_spaces += 1
            continue
        new_spaces += emit_artspace(name_zh, name_en, desc_zh, desc_en, country,
                                    existing_spaces_zh, existing_spaces_en)

    print(f"Artists: wrote {new_artists} file(s), skipped {skipped_artists} (no mention in corpus)")
    print(f"Art spaces: wrote {new_spaces} file(s), skipped {skipped_spaces} (no mention in corpus)")


if __name__ == "__main__":
    main()
