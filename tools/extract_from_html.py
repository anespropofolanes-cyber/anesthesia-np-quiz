#!/usr/bin/env python3
"""從舊題庫 HTML 抽出 12 個 DATA 區塊，寫成 data/questions/<year>_<subject>.json。

來源：專科護理師題庫/anesthesia_quiz_full.html
每個 DATA_<year>_<SUBJECT> 是單行 JSON（const DATA_xxx = {...};）。
本腳本只讀來源檔，絕不寫入舊專案。
"""
import json
import re
import sys
from pathlib import Path

SRC = Path("/Users/huangxinyi/Documents/Claude/Projects/專科護理師題庫/anesthesia_quiz_full.html")
DEST_DIR = Path(__file__).resolve().parent.parent / "data" / "questions"

BLOCK_RE = re.compile(r"^\s*const DATA_(\d{3})_(ADVANCED|GENERAL)\s*=\s*(\{.*\});\s*$")


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    found = {}
    with SRC.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            m = BLOCK_RE.match(line)
            if not m:
                continue
            year, subject = m.group(1), m.group(2).lower()
            data = json.loads(m.group(3))
            key = f"{year}_{subject}"
            # 舊專案 111-114 進階科的 source/image 用 <year>_anesthesia_ 前綴，
            # 109-110 卻用 <year>_advanced_；新專案統一為 <year>_<subject>_
            for q in data.get("questions", []):
                for field in ("source", "image"):
                    if q.get(field):
                        q[field] = q[field].replace(f"{year}_anesthesia_", f"{year}_{subject}_")
            if key in found:
                print(f"錯誤：{key} 出現兩次（第 {found[key]} 行與第 {lineno} 行）")
                sys.exit(1)
            found[key] = lineno
            out = DEST_DIR / f"{key}.json"
            with out.open("w", encoding="utf-8") as g:
                json.dump(data, g, ensure_ascii=False, indent=2)
                g.write("\n")
            n = len(data.get("questions", []))
            print(f"{key}: 第 {lineno} 行 → {out.name}（{n} 題）")

    expected = {f"{y}_{s}" for y in range(109, 115) for s in ("advanced", "general")}
    missing = expected - set(found)
    if missing:
        print(f"錯誤：缺少區塊 {sorted(missing)}")
        sys.exit(1)
    print(f"\n完成：共 {len(found)} 個區塊。")


if __name__ == "__main__":
    main()
