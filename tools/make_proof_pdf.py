#!/usr/bin/env python3
"""產生校對版 PDF：每年一份（含進階＋通論 160 題）＋ 一份特殊題清單。

每題印出題幹、四選項（正解標示）、圖片、解析、分類、難度，並留核對欄位，
供列印後逐題勾核。用 Chrome headless 轉 PDF（CJK 與圖片品質最佳）。

用法：python3 tools/make_proof_pdf.py [年份…]　（預設全部）
"""
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QDIR = ROOT / "data" / "questions"
OUT = ROOT / "proof"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SUBJECT_NAME = {"advanced": "進階專科護理", "general": "專科護理通論"}
DIFF_LABEL = {"easy": "初級", "medium": "中級", "hard": "高級"}

# 配色（使用者指定）：#f2dbe1 粉　#9ac5cd 藍綠　#fcf4d7 奶油
CSS = """
@page { size: A4; margin: 11mm 10mm 10mm 10mm; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "Songti TC", "Songti SC", serif;
       font-size: 10pt; line-height: 1.45; color: #1a1a1a; }
.cover { text-align: center; padding: 55mm 0 0; page-break-after: always; }
.cover h1 { font-size: 26pt; margin: 0 0 6mm; letter-spacing: 2px; }
.cover .rule { width: 40mm; height: 3px; background: #9ac5cd; margin: 0 auto 8mm; }
.cover .sub { font-size: 13pt; color: #555; margin-bottom: 18mm; }
.cover .box { display: inline-block; text-align: left; border: 1px solid #d8c3c9;
              border-top: 4px solid #f2dbe1; background: #fcf4d7;
              padding: 8mm 12mm; font-size: 10pt; line-height: 2; }
h2.paper { font-size: 14pt; margin: 0 0 3mm; padding: 2mm 3.5mm;
           background: #f2dbe1; border-left: 5px solid #9ac5cd; page-break-after: avoid; }
h2.paper + .q { page-break-before: avoid; }
.q { border: 1px solid #ddd; border-radius: 2mm; padding: 2.5mm 3.5mm 2mm;
     margin-bottom: 2.5mm; page-break-inside: avoid; }
.qhead { display: flex; justify-content: space-between; align-items: baseline;
         border-bottom: 1px dotted #ccc; padding-bottom: 1mm; margin-bottom: 1.5mm; }
.qno { font-weight: bold; font-size: 11pt; }
.tags { font-family: "PingFang TC", sans-serif; font-size: 8pt; color: #666; }
.tag { display: inline-block; border: 1px solid #ddd; border-radius: 2mm;
       padding: 0.3mm 2mm; margin-left: 1.5mm; }
.tag.free { background: #fcf4d7; border-color: #d9c47e; color: #7a5c00; }
.tag.multi { background: #9ac5cd; border-color: #6fa4ae; color: #123f47; }
.tag.note { background: #f2dbe1; border-color: #c79aa6; color: #8a4356; }
.stem { margin-bottom: 1.5mm; }
.enote { font-family: "PingFang TC", sans-serif; font-size: 8.5pt; color: #4b6b71;
         background: #eef6f8; border-left: 3px solid #9ac5cd; padding: 1mm 3mm;
         margin: 0 0 2.5mm; }
ol.opts { list-style: none; margin: 0 0 1.5mm; padding: 0; }
ol.opts li { padding: 0.4mm 2mm; margin-bottom: 0.3mm; border-radius: 1.5mm; }
ol.opts li.ok { background: #f2dbe1; font-weight: bold; }
ol.opts li .L { display: inline-block; width: 6mm; font-weight: bold; }
.fig { text-align: center; margin: 1.5mm 0 2mm; }
.fig img { max-width: 75%; max-height: 70mm; border: 1px solid #ccc; }
.fig .cap { font-family: "PingFang TC", sans-serif; font-size: 8pt; color: #666; margin-top: 1mm; }
.ans { font-family: "PingFang TC", sans-serif; font-size: 9pt; margin-bottom: 1mm; }
.ans b { color: #8a4356; }
.exp { font-size: 9pt; background: #fcf4d7; border-left: 3px solid #9ac5cd;
       padding: 1mm 2.5mm; margin-bottom: 1.2mm; }
.exp .h { font-family: "PingFang TC", sans-serif; font-size: 8pt; color: #7a6a3a;
          display: block; margin-bottom: 0.5mm; }
.check { font-family: "PingFang TC", sans-serif; font-size: 8pt; color: #999;
         border-top: 1px dotted #ddd; padding-top: 1mm; }
.check .line { display: inline-block; border-bottom: 1px solid #ddd;
               width: 62%; margin-left: 2mm; }
table.sp { width: 100%; border-collapse: collapse; font-size: 9.5pt;
           font-family: "PingFang TC", sans-serif; margin-bottom: 8mm; }
table.sp th, table.sp td { border: 1px solid #ccc; padding: 1.5mm 2.5mm; text-align: left;
                           vertical-align: top; }
table.sp th { background: #f2dbe1; }
table.sp tr:nth-child(even) td { background: #fdfaf0; }
h3.sec { font-size: 13pt; margin: 6mm 0 3mm; border-bottom: 2px solid #9ac5cd;
         padding-bottom: 1.5mm; }
p.hint { font-family: "PingFang TC", sans-serif; font-size: 9pt; color: #555;
         background: #eef6f8; border-left: 3px solid #9ac5cd; padding: 2mm 3mm;
         margin: 0 0 4mm; }
.grid { display: flex; flex-wrap: wrap; gap: 3mm; }
.cell { width: 90mm; border: 1px solid #ddd; border-radius: 2mm; padding: 2mm;
        page-break-inside: avoid; }
.cell .ref { font-family: "PingFang TC", sans-serif; font-size: 9pt; font-weight: bold;
             background: #f2dbe1; padding: 0.8mm 2mm; border-radius: 1.5mm;
             margin-bottom: 1.5mm; }
.cell img { display: block; max-width: 100%; max-height: 60mm; margin: 0 auto 1.5mm;
            border: 1px solid #eee; }
.cell .fn { font-family: "PingFang TC", monospace; font-size: 7.5pt; color: #999; }
.cell .cap2 { font-family: "PingFang TC", sans-serif; font-size: 8pt; color: #666;
              margin-top: 0.5mm; }
.cell .mark { font-family: "PingFang TC", sans-serif; font-size: 8pt; color: #aaa;
              border-top: 1px dotted #ddd; margin-top: 1.5mm; padding-top: 1mm; }
"""


def esc(s):
    return html.escape(s or "")


def render_question(q, year, subject):
    ans = q["answer"]
    is_free = ans == "送分"
    is_multi = (not is_free) and len(ans) > 1

    tags = [f'<span class="tag">{esc(q["category"])}</span>',
            f'<span class="tag">{DIFF_LABEL.get(q["difficulty"], q["difficulty"])}</span>']
    if is_free:
        tags.insert(0, '<span class="tag free">送分</span>')
    if is_multi:
        tags.insert(0, f'<span class="tag multi">多答案 {esc(ans)}</span>')
    if q.get("note"):
        tags.insert(0, '<span class="tag note">疑義</span>')
    if q.get("image"):
        tags.append(f'<span class="tag">{esc(q["image"])}</span>')

    parts = [f'<div class="q"><div class="qhead">'
             f'<span class="qno">Q{q["id"]}</span>'
             f'<span class="tags">{"".join(tags)}</span></div>',
             f'<div class="stem">{esc(q["question"])}</div>']

    if q.get("editor_note"):
        parts.append(f'<p class="enote">編註：{esc(q["editor_note"])}</p>')

    parts.append("<ol class=\"opts\">")
    for letter in "ABCD":
        ok = "" if is_free else (" ok" if letter in ans else "")
        parts.append(f'<li class="{ok.strip()}"><span class="L">({letter})</span>'
                     f'{esc(q["options"][letter])}</li>')
    parts.append("</ol>")

    if q.get("image"):
        cap = f'<div class="cap">{esc(q["image_caption"])}</div>' if q.get("image_caption") else ""
        parts.append(f'<div class="fig"><img src="../images/{esc(q["image"])}">{cap}</div>')

    ans_txt = "送分（全題給分）" if is_free else "、".join(ans)
    parts.append(f'<div class="ans">正解：<b>{esc(ans_txt)}</b></div>')
    parts.append(f'<div class="exp"><span class="h">解析</span>{esc(q["explanation"])}</div>')
    if q.get("note"):
        parts.append(f'<div class="exp"><span class="h">疑義說明</span>{esc(q["note"])}</div>')
    parts.append('<div class="check">□ 題幹選項相符　□ 答案正確　□ 解析正確　'
                 '訂正：<span class="line"></span></div>')
    parts.append("</div>")
    return "\n".join(parts)


def build_year(year):
    body = [f'<div class="cover"><h1>{year} 年麻醉專科護理師甄審</h1>'
            f'<div class="rule"></div>'
            f'<div class="sub">題庫校對版　進階專科護理 ＋ 專科護理通論　共 160 題</div>'
            f'<div class="box">核對重點：<br>'
            f'1. 題幹與選項文字是否與原考題一致<br>'
            f'2. 正解是否正確（送分／多答案已標示）<br>'
            f'3. 解析內容是否正確、是否需補充<br>'
            f'4. 圖片是否清楚、是否對應正確題目<br>'
            f'5. 分類標籤是否合理（新分類將於下一階段重做）</div></div>']

    for subject in ("advanced", "general"):
        data = json.loads((QDIR / f"{year}_{subject}.json").read_text("utf-8"))
        body.append(f'<h2 class="paper">{year} 年　{SUBJECT_NAME[subject]}（80 題）</h2>')
        body += [render_question(q, year, subject) for q in data["questions"]]

    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<title>{year}年題庫校對版</title><style>{CSS}</style></head>'
            f'<body>{"".join(body)}</body></html>')


def build_special():
    free, multi, note, images = [], [], [], []
    for year in range(109, 115):
        for subject in ("advanced", "general"):
            data = json.loads((QDIR / f"{year}_{subject}.json").read_text("utf-8"))
            for q in data["questions"]:
                ref = f"{year} {SUBJECT_NAME[subject]} Q{q['id']}"
                if q["answer"] == "送分":
                    free.append((ref, q["question"][:60], q["explanation"]))
                elif len(q["answer"]) > 1:
                    multi.append((ref, q["answer"], q["question"][:60], q["explanation"]))
                if q.get("note"):
                    note.append((ref, q["note"]))
                if q.get("image"):
                    images.append((ref, q["image"], q.get("image_caption", "")))

    def table(head, rows):
        h = "".join(f"<th>{c}</th>" for c in head)
        body = "".join("<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in r) + "</tr>"
                       for r in rows)
        return f'<table class="sp"><tr>{h}</tr>{body}</table>'

    body = ['<div class="cover"><h1>特殊題清單</h1>'
            '<div class="rule"></div>'
            '<div class="sub">送分題、多答案題、疑義題、圖片題　重點核對用</div>'
            '<div class="box">本清單彙整最需要確認的題目。<br>'
            '送分與多答案皆依衛生福利部疑義試題答案公告認定。<br>'
            '圖片題須逐張確認圖檔清晰度與對應題號。</div></div>',
            f'<h3 class="sec">一、送分題（{len(free)} 題）</h3>',
            table(["題號", "題幹（節錄）", "送分理由"], free),
            f'<h3 class="sec">二、多答案題（{len(multi)} 題）</h3>',
            table(["題號", "答案", "題幹（節錄）", "說明"], multi),
            f'<h3 class="sec">三、疑義題註記（{len(note)} 題）</h3>',
            table(["題號", "註記"], note),
            f'<h3 class="sec">四、圖片題總覽（{len(images)} 題）</h3>',
            '<p class="hint">請逐張確認：① 圖是否清晰可判讀　② 是否對應正確題號　'
            '③ 是否誤含題幹文字或「試題公告 僅供參考」浮水印（需重新裁切者請圈起）</p>',
            '<div class="grid">']
    for ref, img, cap in images:
        body.append(f'<div class="cell"><div class="ref">{esc(ref)}</div>'
                    f'<img src="../images/{esc(img)}">'
                    f'<div class="fn">{esc(img)}</div>'
                    + (f'<div class="cap2">{esc(cap)}</div>' if cap else "")
                    + '<div class="mark">□ 清晰　□ 對應正確　□ 無雜訊</div></div>')
    body.append("</div>")
    return ('<!doctype html><html><head><meta charset="utf-8">'
            f'<title>特殊題清單</title><style>{CSS}</style></head>'
            f'<body>{"".join(body)}</body></html>')


def to_pdf(html_path, pdf_path):
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                   check=True, capture_output=True)


def main():
    OUT.mkdir(exist_ok=True)
    years = [int(a) for a in sys.argv[1:]] or list(range(109, 115))

    for year in years:
        hp = OUT / f"{year}_校對版.html"
        hp.write_text(build_year(year), encoding="utf-8")
        pp = OUT / f"{year}_校對版.pdf"
        to_pdf(hp, pp)
        print(f"{pp.name}　{pp.stat().st_size / 1024 / 1024:.1f} MB")

    hp = OUT / "特殊題清單.html"
    hp.write_text(build_special(), encoding="utf-8")
    pp = OUT / "特殊題清單.pdf"
    to_pdf(hp, pp)
    print(f"{pp.name}　{pp.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
