#!/usr/bin/env python3
"""修正圖說（image_caption）。

原則：**圖說只描述看得到的東西，不做診斷** ——因為診斷往往就是答案本身。

發現的問題：
1. 109_general_Q72 圖說寫「高峻 T 波」，但該題答案已更正為 B（ST 段抬高之急性冠心症），
   圖說與解析互相矛盾，且描述的心電圖型態根本不對。
2. 113_advanced_Q16 題目問「是何種心律不整？」，圖說卻直接寫出答案「完全房室傳導阻滯」。
3. 109_general_Q53 題目問「造成心電圖最可能原因」，圖說寫「高峻 T 波」等於把判讀步驟做完了。
"""
import json
import sys
from pathlib import Path

QDIR = Path(__file__).resolve().parent.parent / "data" / "questions"

FIXES = [
    ("109_general", 72,
     "心電圖：高峻 T 波（peaked T wave）",
     "心電圖：單一導程節律帶，ST 段抬高並與寬鈍 T 波融合",
     "原圖說「高峻 T 波」與更正後的答案 B（急性冠心症）矛盾，且與圖上實際波形不符"),

    ("113_advanced", 16,
     "圖（三）：完全房室傳導阻滯（complete AV block）心電圖",
     "圖（三）：心電圖節律帶（觀察 P 波與 QRS 的關係及 PR 間期是否固定）",
     "原圖說直接寫出答案（本題問的正是「是何種心律不整」）"),

    ("109_general", 53,
     "心電圖：高峻 T 波（peaked T wave）",
     "心電圖：術前 12 導程之單一導程節律帶（注意 T 波型態與 QRS 寬度）",
     "原圖說已完成判讀步驟，等於提示答案（本題問造成此心電圖的最可能原因）"),
]


def main():
    changed, errors = {}, []
    for fname, qid, old, new, why in FIXES:
        data = changed.setdefault(fname, json.loads((QDIR / f"{fname}.json").read_text("utf-8")))
        q = next((x for x in data["questions"] if x["id"] == qid), None)
        if q is None or q.get("image_caption") != old:
            errors.append(f"{fname} Q{qid}: 原圖說不符（目前為「{q.get('image_caption') if q else '找不到題目'}」）")
            continue
        q["image_caption"] = new
        prev = q.get("review_note", "")
        q["review_note"] = (prev + "；" if prev else "") + f"2026-07-31 圖說修正：{why}"
        print(f"修正 {fname} Q{qid} 圖說")

    if errors:
        print("\n未套用任何變更：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    for fname, data in changed.items():
        (QDIR / f"{fname}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"寫回 {fname}.json")


if __name__ == "__main__":
    main()
