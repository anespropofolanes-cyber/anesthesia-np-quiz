#!/usr/bin/env python3
"""驗證 data/questions/*.json 的結構完整性。

檢查項目：
1. 12 個檔案齊全，每檔 meta.total == 80 且 questions 恰為 80 題
2. 每題 id 連續（1..80）、必要欄位齊全
3. options 恰為 A/B/C/D 四鍵且值非空
4. answer 格式合法：A-D 單一、A-D 多字元組合（去重、遞增）、或「送分」
5. image 欄位為裸檔名（不含路徑分隔符），且檔案存在於 images/
6. 特殊題統計（送分／多答案／疑義 note）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QDIR = ROOT / "data" / "questions"
IMG_DIR = ROOT / "images"

REQUIRED_FIELDS = ["id", "question", "options", "answer", "explanation",
                   "difficulty", "source"]
# 分類欄位：Phase 2 之前是 category；之後改為 topic + subtopic（舊值留在 legacy_category）
ANSWER_RE = re.compile(r"^[A-D]{1,4}$")
DIFFICULTIES = {"easy", "medium", "hard"}


def check_block(path, errors, stats):
    data = json.loads(path.read_text(encoding="utf-8"))
    name = path.stem
    year, subject = name.split("_")
    meta = data.get("meta", {})
    qs = data.get("questions", [])

    if meta.get("total") != 80:
        errors.append(f"{name}: meta.total = {meta.get('total')}（應為 80）")
    if str(meta.get("year")) != year or meta.get("subject") != subject:
        errors.append(f"{name}: meta year/subject 與檔名不符 → {meta.get('year')}/{meta.get('subject')}")
    if len(qs) != 80:
        errors.append(f"{name}: 共 {len(qs)} 題（應為 80）")

    for i, q in enumerate(qs, 1):
        tag = f"{name} Q{q.get('id', '?')}"
        if q.get("id") != i:
            errors.append(f"{tag}: id 不連續（第 {i} 個位置是 id={q.get('id')}）")
        for f in REQUIRED_FIELDS:
            if f not in q or q[f] in (None, ""):
                errors.append(f"{tag}: 缺欄位 {f}")
        opts = q.get("options", {})
        if sorted(opts.keys()) != ["A", "B", "C", "D"]:
            errors.append(f"{tag}: options 鍵異常 {sorted(opts.keys())}")
        elif any(not str(v).strip() for v in opts.values()):
            errors.append(f"{tag}: 有空白選項")
        ans = q.get("answer", "")
        if ans == "送分":
            stats["free"].append(q.get("source", tag))
        elif ANSWER_RE.match(ans):
            if len(set(ans)) != len(ans) or "".join(sorted(ans)) != ans:
                errors.append(f"{tag}: 多答案格式異常「{ans}」（應為遞增且不重複，如 BC）")
            if len(ans) > 1:
                stats["multi"].append(f"{q.get('source', tag)}={ans}")
        else:
            errors.append(f"{tag}: answer 格式非法「{ans}」")
        if not (q.get("category") or (q.get("topic") and q.get("subtopic"))):
            errors.append(f"{tag}: 缺分類（需有 category，或 topic＋subtopic）")
        if q.get("difficulty") not in DIFFICULTIES:
            errors.append(f"{tag}: difficulty 異常「{q.get('difficulty')}」")
        src_expect = f"{year}_{subject}_Q{q.get('id')}"
        if q.get("source") != src_expect:
            errors.append(f"{tag}: source「{q.get('source')}」≠ 預期「{src_expect}」")
        img = q.get("image")
        if img:
            stats["image"].append(img)
            if "/" in img or "\\" in img:
                errors.append(f"{tag}: image 含路徑「{img}」（應為裸檔名）")
            elif not (IMG_DIR / img).is_file():
                errors.append(f"{tag}: 圖檔不存在 images/{img}")
        if q.get("note"):
            stats["note"].append(q.get("source", tag))

    return len(qs)


def main():
    files = sorted(QDIR.glob("*.json"))
    expected = {f"{y}_{s}" for y in range(109, 115) for s in ("advanced", "general")}
    got = {p.stem for p in files}
    errors = []
    if got != expected:
        errors.append(f"檔案不齊：缺 {sorted(expected - got)}，多 {sorted(got - expected)}")

    stats = {"free": [], "multi": [], "image": [], "note": []}
    total = sum(check_block(p, errors, stats) for p in files)

    print(f"檔案數：{len(files)}　總題數：{total}")
    print(f"送分題 {len(stats['free'])}：{', '.join(stats['free'])}")
    print(f"多答案題 {len(stats['multi'])}：{', '.join(stats['multi'])}")
    print(f"圖片題 {len(stats['image'])}　疑義 note 題 {len(stats['note'])}：{', '.join(stats['note'])}")

    # 圖檔反向檢查：images/ 內有沒有沒被引用的檔案
    if IMG_DIR.is_dir():
        used = set(stats["image"])
        orphan = sorted(p.name for p in IMG_DIR.iterdir()
                        if p.is_file() and not p.name.startswith(".") and p.name not in used)
        if orphan:
            print(f"未被引用的圖檔 {len(orphan)}：{', '.join(orphan)}")

    if errors:
        print(f"\n發現 {len(errors)} 個問題：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("\n全部檢查通過。")


if __name__ == "__main__":
    main()
