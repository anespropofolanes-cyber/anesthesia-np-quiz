#!/usr/bin/env python3
"""從考題 PDF 重新抽取 80 題（題幹＋四選項），輸出 audit/parsed_<year>_<subject>.json。

格式與舊專案 audit_data/parsed_*.json 一致：{"<題號>": {"stem": ..., "options": {A..D}}}
用法：python3 tools/parse_pdf.py <pdf路徑> <year> <subject>
      python3 tools/parse_pdf.py --all      # 抽全部 12 份
"""
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "audit"
SRC_PDF_ROOT = Path("/Users/huangxinyi/Documents/Claude/Projects/專科護理師題庫/source_pdfs")

# 頁首/頁尾雜訊行
NOISE_RE = re.compile(
    r"^(麻醉科\s|第\s*\d+\s*頁|共\s*\d+\s*頁|.*共\s*\d+\s*頁\s*$|注意：考試開始|入場證號碼|考試開始鈴)"
)
# 題號行如「12. 下列…」；(?!\d) 排除換行後接續的小數（如「0.5 ％ bupivacaine」）
QNUM_RE = re.compile(r"^(\d{1,2})\.(?!\d)\s*")
OPT_RE = re.compile(r"\(([A-D])\)\s*")


def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for page in doc[1:]:  # 第 1 頁是封面＋注意事項（含 1.-7. 編號清單，會干擾題號解析），跳過
        for raw in page.get_text().splitlines():
            line = raw.replace("ˉ", " ").strip()
            if not line or NOISE_RE.match(line):
                continue
            lines.append(line)
    return lines


def parse_questions(lines):
    """把行流切成 {qnum: 全文字串}，再各自切出題幹與選項。"""
    problems_stray = []
    blocks = {}
    cur = None
    buf = []
    expected = 1
    skipping = False  # 遇到「已解析過的題號重新出現」→ 殘留重複頁，跳到下一個預期題號
    for line in lines:
        m = QNUM_RE.match(line)
        if m and int(m.group(1)) == expected:
            if cur is not None:
                blocks[cur] = " ".join(buf)
            cur = expected
            expected += 1
            buf = [QNUM_RE.sub("", line)]
            skipping = False
        elif m and cur is not None and int(m.group(1)) < cur:
            # 例如 113_advanced.pdf 第 3 頁是 Q1 的重複殘留頁
            problems_stray.append(f"跳過殘留內容：Q{cur} 之後出現重複的「{line[:30]}…」")
            skipping = True
        elif skipping:
            continue
        elif cur is not None:
            if "【以下空白】" in line:
                line = line.split("【以下空白】")[0].strip()
                if line:
                    buf.append(line)
                break
            buf.append(line)
        # cur is None → 仍在前言，丟棄
    if cur is not None:
        blocks[cur] = " ".join(buf)

    parsed = {}
    problems = list(problems_stray)
    for qnum, text in blocks.items():
        parts = OPT_RE.split(text)
        # parts = [stem, 'A', txtA, 'B', txtB, ...]
        stem = parts[0].strip()
        opts = {}
        for i in range(1, len(parts) - 1, 2):
            letter, val = parts[i], parts[i + 1].strip()
            if letter in opts:
                problems.append(f"Q{qnum}: 選項 {letter} 重複出現（題幹或選項含 ({letter}) 字樣）")
            opts[letter] = val
        if sorted(opts.keys()) != ["A", "B", "C", "D"]:
            problems.append(f"Q{qnum}: 選項不齊 {sorted(opts.keys())}")
        parsed[str(qnum)] = {"stem": stem, "options": opts}
    return parsed, problems


def run_one(pdf_path, year, subject):
    lines = extract_text(pdf_path)
    parsed, problems = parse_questions(lines)
    out = OUT_DIR / f"parsed_{year}_{subject}.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "OK" if len(parsed) == 80 and not problems else "有問題"
    print(f"{year}_{subject}: {len(parsed)} 題 → {out.name}　[{status}]")
    for p in problems:
        print(f"    ! {p}")
    return len(parsed) == 80


def main():
    if sys.argv[1:] == ["--all"]:
        ok = True
        for year in range(109, 115):
            for subject in ("advanced", "general"):
                pdf = SRC_PDF_ROOT / str(year) / f"{year}_{subject}.pdf"
                ok &= run_one(pdf, year, subject)
        sys.exit(0 if ok else 1)
    pdf, year, subject = sys.argv[1], sys.argv[2], sys.argv[3]
    run_one(Path(pdf), year, subject)


if __name__ == "__main__":
    main()
