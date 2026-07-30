#!/usr/bin/env python3
"""用官方【標準答案】卡逐題核對題庫 answer 欄位。

答案卡 PDF 為 10 欄表格（題號列 / 答案列交錯），PyMuPDF 抽出的 token 順序即為
「10 個題號 → 10 個答案」重複 8 次。部分列會被抽成單行（如「24 送分 34」），
故先把全文攤平成 token 流再配對。

用法：python3 tools/verify_answer_keys.py <答案卡PDF> <year> <subject>
      python3 tools/verify_answer_keys.py --scan <目錄>   # 掃描目錄內所有答案卡並自動判別年份科目
"""
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
QDIR = ROOT / "data" / "questions"

ANS_RE = re.compile(r"^(?:[A-D]{1,4}|送分)$")


def _parse_interleaved(toks):
    """佈局 A：題號與答案逐一交錯（題號 答案 題號 答案 …）。"""
    key, i = {}, 0
    while i < len(toks) - 1:
        a, b = toks[i], toks[i + 1]
        if re.fullmatch(r"\d{1,2}", a) and ANS_RE.match(b):
            n = int(a)
            if 1 <= n <= 80 and n not in key:
                key[n] = b
                i += 2
                continue
        i += 1
    return key


def _parse_blocks(toks):
    """佈局 B：一整列題號（1..10）後接一整列答案。"""
    key, i = {}, 0
    while i < len(toks):
        nums, j = [], i
        while (j < len(toks) and re.fullmatch(r"\d{1,2}", toks[j])
               and len(nums) < 10
               and (not nums or int(toks[j]) == nums[-1] + 1)):
            nums.append(int(toks[j]))
            j += 1
        if len(nums) >= 3:
            ans, k = [], j
            while k < len(toks) and len(ans) < len(nums) and ANS_RE.match(toks[k]):
                ans.append(toks[k])
                k += 1
            if len(ans) == len(nums):
                key.update(dict(zip(nums, ans)))
                i = k
                continue
        i += 1
    return key


def parse_key(pdf_path):
    """回傳 {題號: 答案}。兩種表格佈局都試，取抓到題數較多者。
    兩者都成功時交叉檢查，有衝突就印出警告（避免誤判）。"""
    doc = fitz.open(pdf_path)
    text = " ".join(p.get_text() for p in doc).replace("\n", " ")
    toks = [t for t in re.split(r"\s+", text) if t]
    a, b = _parse_interleaved(toks), _parse_blocks(toks)
    if len(a) >= 70 and len(b) >= 70:
        conflict = {q for q in set(a) & set(b) if a[q] != b[q]}
        if conflict:
            print(f"  ⚠️ {Path(pdf_path).name}：兩種解析法對 Q{sorted(conflict)} 結果不同，需人工確認")
    return a if len(a) >= len(b) else b


def detect(pdf_path, key):
    """從 PDF 文字判斷年份與科目。"""
    text = " ".join(p.get_text() for p in fitz.open(pdf_path))
    m = re.search(r"(\d{3})\s*年度", text)
    year = m.group(1) if m else None
    if "進階專科護理" in text:
        subject = "advanced"
    elif "專科護理通論" in text:
        subject = "general"
    else:
        subject = None
    return year, subject


def verify(year, subject, key, label=""):
    qfile = QDIR / f"{year}_{subject}.json"
    if not qfile.is_file():
        print(f"  跳過：找不到 {qfile.name}")
        return None
    quiz = json.loads(qfile.read_text(encoding="utf-8"))["questions"]
    missing = sorted(set(range(1, 81)) - set(key))
    diffs = [(q["id"], q["answer"], key[q["id"]])
             for q in quiz if q["id"] in key and key[q["id"]] != q["answer"]]
    status = "一致" if not diffs else f"⚠️ {len(diffs)} 題不符"
    print(f"  {year}_{subject}：答案卡 {len(key)}/80 題"
          + (f"（缺 {missing}）" if missing else "")
          + f"　→ {status}")
    for qid, mine, official in diffs:
        print(f"    Q{qid}: 題庫「{mine}」　官方「{official}」")
    return diffs


def main():
    if sys.argv[1] == "--scan":
        pdfs = sorted(Path(sys.argv[2]).glob("*.pdf"))
        results = {}
        for p in pdfs:
            key = parse_key(p)
            if len(key) < 60:  # 不是完整答案卡
                continue
            year, subject = detect(p, key)
            if not (year and subject):
                print(f"{p.name}：抓到 {len(key)} 題但無法判別年份/科目，略過")
                continue
            tag = f"{year}_{subject}"
            if tag in results:  # 同一卷有多份答案卡（疑義更正版），保留題數較多者
                if len(key) <= len(results[tag][0]):
                    continue
            results[tag] = (key, p.name)
        print(f"\n共找到 {len(results)} 卷的完整答案卡：\n")
        all_diffs = {}
        for tag in sorted(results):
            key, fname = results[tag]
            year, subject = tag.split("_")
            print(f"[{fname}]")
            d = verify(year, subject, key)
            if d:
                all_diffs[tag] = d
        print(f"\n{'=' * 50}")
        if all_diffs:
            total = sum(len(v) for v in all_diffs.values())
            print(f"總計 {total} 題答案與官方不符：")
            for tag, ds in all_diffs.items():
                for qid, mine, official in ds:
                    print(f"  {tag}_Q{qid}: 題庫「{mine}」 官方「{official}」")
        else:
            print("所有可核對的卷別，答案全部與官方一致。")
        return 0 if not all_diffs else 2

    pdf, year, subject = sys.argv[1], sys.argv[2], sys.argv[3]
    key = parse_key(Path(pdf))
    print(f"[{Path(pdf).name}]")
    verify(year, subject, key)
    return 0


if __name__ == "__main__":
    sys.exit(main())
