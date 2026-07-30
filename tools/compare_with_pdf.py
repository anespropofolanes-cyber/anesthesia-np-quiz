#!/usr/bin/env python3
"""逐題比對 data/questions/*.json 與 audit/parsed_*.json（PDF 原文），並自動分類差異。

正規化時忽略純格式差異：全形半形、空白、標點變體、CJK 相容字、異體字、
PDF 浮水印（「試題公告 僅供參考」）、浮動圖說（「圖（一）」）。

剩餘差異自動分為三類：
- PDF 掉字：PDF 文字為題庫的子序列（110 年 PDF 文字層大量掉字，題庫較完整可信）
- 題庫省略：題庫文字為 PDF 的子序列（題庫刪去了 PDF 原有內容，需判斷是否刻意精簡）
- 用字不同：兩者互不為子序列（最可疑，需人工判讀；含 PDF 錯字已被題庫修正的情形）

輸出 audit/compare_report.md。
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QDIR = ROOT / "data" / "questions"
ADIR = ROOT / "audit"
SPECIAL_ANSWERS = Path("/Users/huangxinyi/Documents/Claude/Projects/專科護理師題庫"
                       "/audit_data/special_answers.json")

PUNCT_MAP = str.maketrans({
    "（": "(", "）": ")", "［": "[", "］": "]", "，": ",", "：": ":", "；": ";",
    "？": "?", "！": "!", "、": ",", "。": ".", "％": "%", "～": "~", "／": "/",
    "–": "-", "−": "-", "‐": "-", "—": "-", "‑": "-",
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "°": "", "µ": "u", "μ": "u",
    # 異體字／簡繁混用（PDF 排版偶見）
    "横": "橫", "内": "內", "钾": "鉀",
})
# 比對時一律移除的標點（換行處逗號有無屬排版差異，不是內容差異）
DROP_PUNCT = re.compile(r"[,.:;?!'\"()\[\]~/\-]")
# PDF 頁面浮水印
WATERMARK = re.compile(r"(試題公告|公告試題)僅供參考")
# 浮動圖說：PDF 把「圖（一）」這類圖片標題也抽成文字，位置飄移
FIGURE_LABEL = re.compile(r"圖\(?[一二三四五六七八九十\d]+\)?")


def norm(s, drop_punct=True):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(PUNCT_MAP)
    s = re.sub(r"\s+", "", s)
    s = WATERMARK.sub("", s)
    s = FIGURE_LABEL.sub("", s)
    if drop_punct:
        s = DROP_PUNCT.sub("", s)
    return s.lower()


def is_subseq(small, big):
    """small 是否為 big 的子序列（用於判斷單邊掉字）。"""
    it = iter(big)
    return all(ch in it for ch in small)


def classify(quiz_txt, pdf_txt):
    q, p = norm(quiz_txt), norm(pdf_txt)
    if q == p:
        return None
    if is_subseq(p, q):
        return "PDF 掉字"
    if is_subseq(q, p):
        return "題庫省略"
    return "用字不同"


def compare_block(year, subject, issues):
    quiz = json.loads((QDIR / f"{year}_{subject}.json").read_text(encoding="utf-8"))["questions"]
    pdf = json.loads((ADIR / f"parsed_{year}_{subject}.json").read_text(encoding="utf-8"))
    tag = f"{year}_{subject}"
    counts = {"PDF 掉字": 0, "題庫省略": 0, "用字不同": 0, "圖片選項": 0}

    for q in quiz:
        p = pdf.get(str(q["id"]))
        if p is None:
            issues.append((tag, str(q["id"]), "缺 PDF 對應題", "題幹", "", ""))
            continue

        kind = classify(q["question"], p["stem"])
        if kind:
            counts[kind] += 1
            issues.append((tag, str(q["id"]), kind, "題幹", q["question"], p["stem"]))

        for letter in "ABCD":
            pdf_opt = p["options"].get(letter, "")
            if not pdf_opt.strip():
                counts["圖片選項"] += 1  # PDF 中選項是圖片，無文字可比
                continue
            kind = classify(q["options"].get(letter, ""), pdf_opt)
            if kind:
                counts[kind] += 1
                issues.append((tag, str(q["id"]), kind, f"選項 {letter}",
                               q["options"].get(letter, ""), pdf_opt))
    return counts


def special_answer_section():
    special = json.loads(SPECIAL_ANSWERS.read_text(encoding="utf-8"))
    quiz_special = {}
    for qf in sorted(QDIR.glob("*.json")):
        year, subject = qf.stem.split("_")
        for q in json.loads(qf.read_text(encoding="utf-8"))["questions"]:
            if q["answer"] == "送分" or len(q["answer"]) > 1:
                quiz_special[f"{year}_{subject}_Q{q['id']}"] = q["answer"]
    lines = ["", "## 特殊答案（送分／多答案）核對", "",
             f"題庫中特殊答案題共 {len(quiz_special)} 題：", "",
             "| 題號 | 題庫答案 |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(quiz_special.items())]
    lines += ["", "衛福部疑義公告整理檔 `special_answers.json` 原始內容（供人工核對）：", "",
              "```json", json.dumps(special, ensure_ascii=False, indent=2), "```"]
    return lines


def main():
    issues = []
    summary = []
    for year in range(109, 115):
        for subject in ("advanced", "general"):
            summary.append((f"{year}_{subject}", compare_block(year, subject, issues)))

    tot = {k: sum(c[k] for _, c in summary) for k in
           ("PDF 掉字", "題庫省略", "用字不同", "圖片選項")}

    out = ["# 題庫 ↔ PDF 原文比對報告", "",
           "正規化後比對（忽略全形半形、空白、標點、異體字、PDF 浮水印、浮動圖說）。", "",
           "差異分類說明：", "",
           "- **PDF 掉字**：PDF 文字為題庫的子序列 → PDF 文字層有缺字，題庫較完整（可信）",
           "- **題庫省略**：題庫文字為 PDF 的子序列 → 題庫刪去 PDF 原有內容（須判斷是否刻意精簡）",
           "- **用字不同**：互不為子序列 → 最可疑，須人工判讀"
           "（也包含 PDF 本身錯字、題庫已修正的情形）", "",
           "## 各卷摘要", "",
           "| 卷別 | PDF 掉字 | 題庫省略 | 用字不同 | PDF 圖片選項 |", "|---|---|---|---|---|"]
    for name, c in summary:
        out.append(f"| {name} | {c['PDF 掉字']} | {c['題庫省略']} | {c['用字不同']} | {c['圖片選項']} |")
    out += ["| **合計** | "
            f"**{tot['PDF 掉字']}** | **{tot['題庫省略']}** | **{tot['用字不同']}** | "
            f"**{tot['圖片選項']}** |", ""]

    for kind in ("用字不同", "題庫省略", "PDF 掉字"):
        rows = [i for i in issues if i[2] == kind]
        out += [f"## {kind}（{len(rows)} 處）", ""]
        if not rows:
            out += ["無。", ""]
            continue
        for tag, qid, _, field, quiz_txt, pdf_txt in rows:
            out += [f"### {tag} Q{qid} {field}", "",
                    f"- 題庫：`{quiz_txt}`", f"- PDF ：`{pdf_txt}`", ""]

    out += special_answer_section()
    report = ADIR / "compare_report.md"
    report.write_text("\n".join(out) + "\n", encoding="utf-8")

    for name, c in summary:
        print(f"{name}: 掉字{c['PDF 掉字']:>3} 省略{c['題庫省略']:>2} "
              f"用字不同{c['用字不同']:>2} 圖片選項{c['圖片選項']:>2}")
    print(f"\n合計：PDF 掉字 {tot['PDF 掉字']}、題庫省略 {tot['題庫省略']}、"
          f"用字不同 {tot['用字不同']} → {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
