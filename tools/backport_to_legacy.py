#!/usr/bin/env python3
"""把新版已修正的內容移植回舊版單檔 HTML（np 倉庫）。

舊版與新版的差異：
- 舊版 111–114 進階科的 source／image 用 `_anesthesia_` 前綴，新版統一為 `_advanced_`
- 舊版用 `category` 欄位驅動篩選與標籤，新版改用 `topic`／`subtopic`
  → 移植時**保留舊版的 category 不動**，只更新內容欄位
- 新版把題庫自加的圖說註解移到 `editor_note`，舊版 renderer 不認得
  → 併回題幹（維持舊版原本的呈現）

移植內容：answer、explanation、question、options、image_caption
另外修正舊版程式碼的送分判定錯誤。

用法：python3 tools/backport_to_legacy.py <np倉庫路徑> [--dry-run]
"""
import json
import re
import sys
from pathlib import Path

NEW_QDIR = Path(__file__).resolve().parent.parent / "data" / "questions"
BLOCK_RE = re.compile(r"^(\s*const DATA_(\d{3})_(ADVANCED|GENERAL)\s*=\s*)(\{.*\})(;\s*)$", re.S)


def load_new():
    """回傳 {正規化source: 新版題目}。"""
    out = {}
    for f in sorted(NEW_QDIR.glob("*.json")):
        for q in json.loads(f.read_text(encoding="utf-8"))["questions"]:
            out[q["source"]] = q
    return out


def norm_src(s):
    """舊版 113_anesthesia_Q2 → 新版 113_advanced_Q2。"""
    return re.sub(r"_anesthesia_", "_advanced_", s)


def main():
    repo = Path(sys.argv[1])
    dry = "--dry-run" in sys.argv
    html = repo / "index.html"
    new = load_new()

    lines = html.read_text(encoding="utf-8").splitlines(keepends=True)
    stats = {"answer": 0, "explanation": 0, "question": 0, "options": 0,
             "editor_note": 0, "image_caption": 0}
    unmatched = []

    for i, line in enumerate(lines):
        m = BLOCK_RE.match(line)
        if not m:
            continue
        head, tail = m.group(1), m.group(5)
        data = json.loads(m.group(4))

        for q in data["questions"]:
            n = new.get(norm_src(q["source"]))
            if n is None:
                unmatched.append(q["source"])
                continue

            if q["answer"] != n["answer"]:
                print(f"  答案 {q['source']}: {q['answer']} → {n['answer']}")
                q["answer"] = n["answer"]
                stats["answer"] += 1

            if q["explanation"] != n["explanation"]:
                q["explanation"] = n["explanation"]
                stats["explanation"] += 1

            # 新版把非考題原文的註解抽到 editor_note，舊版沒有這個欄位，
            # 併回題幹末尾以維持舊版原本的呈現方式
            newq = n["question"]
            if n.get("editor_note"):
                newq += f"（{n['editor_note']}）"
                stats["editor_note"] += 1
            if q["question"] != newq:
                q["question"] = newq
                stats["question"] += 1

            if q["options"] != n["options"]:
                q["options"] = dict(n["options"])
                stats["options"] += 1

            if n.get("image_caption") and q.get("image_caption") != n["image_caption"]:
                q["image_caption"] = n["image_caption"]
                stats["image_caption"] += 1

        lines[i] = head + json.dumps(data, ensure_ascii=False,
                                     separators=(", ", ": ")) + tail

    src = "".join(lines)

    # 送分判定：舊版 q.answer.split('') 拿 A-D 比對「送分」兩字，永遠不成立
    old_fn = "function isCorrect(q, ans) {\n  return q.answer.split('').includes(ans);\n}"
    new_fn = ("function isCorrect(q, ans) {\n"
              "  // 「送分」為衛福部公告全體給分，一律計為正確；\n"
              "  // 多答案如 \"BC\" 則任一即對。\n"
              "  if (q.answer === '送分') return true;\n"
              "  return !!ans && q.answer.includes(ans);\n"
              "}")
    if old_fn in src:
        src = src.replace(old_fn, new_fn)
        stats["送分判定"] = 1
    elif "if (q.answer === '送分') return true;" in src:
        stats["送分判定"] = "已修過"
    else:
        stats["送分判定"] = "⚠️ 找不到原函式，請手動確認"

    print("\n移植統計：")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if unmatched:
        print(f"  ⚠️ 對不到新版的題目 {len(unmatched)}：{unmatched[:5]}")

    if dry:
        print("\n（dry-run，未寫檔）")
        return
    html.write_text(src, encoding="utf-8")
    print(f"\n已寫回 {html}")


if __name__ == "__main__":
    main()
