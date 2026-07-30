#!/usr/bin/env python3
"""把子代理產出的分類指派套用到題庫，並嚴格驗證。

輸入：audit/taxonomy_assign/*.json，格式為
  { "<source>": {"topic": "<topic_id>", "subtopic": "<subtopic_id>"}, ... }

驗證項目：
- topic/subtopic 必須存在於 data/taxonomy.json，且 subtopic 屬於該 topic
- 960 題全部有指派、無重複、無多餘
套用後把舊的 category 欄位保留為 legacy_category。

用法：python3 tools/apply_taxonomy.py [--dry-run]
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QDIR = ROOT / "data" / "questions"
ADIR = ROOT / "audit" / "taxonomy_assign"


def load_taxonomy():
    t = json.loads((ROOT / "data" / "taxonomy.json").read_text(encoding="utf-8"))
    valid = {tp["id"]: {s["id"] for s in tp["subtopics"]} for tp in t["topics"]}
    names = {tp["id"]: tp["name"] for tp in t["topics"]}
    sub_names = {(tp["id"], s["id"]): s["name"] for tp in t["topics"] for s in tp["subtopics"]}
    return valid, names, sub_names


def main():
    dry = "--dry-run" in sys.argv
    valid, names, sub_names = load_taxonomy()

    assign = {}
    year_files = sorted(f for f in ADIR.glob("*.json") if not f.name.startswith("_"))
    for f in year_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        dup = set(data) & set(assign)
        if dup:
            sys.exit(f"錯誤：{f.name} 與先前檔案重複指派 {sorted(dup)[:5]}")
        assign.update(data)
    print(f"讀入 {len(assign)} 筆指派（來自 {len(year_files)} 個年度檔）")

    # 一致性覆核的修正清單（覆蓋年度檔的指派）
    patch_file = ADIR / "_consistency_patch.json"
    if patch_file.is_file():
        patch = json.loads(patch_file.read_text(encoding="utf-8"))
        unknown = sorted(set(patch) - set(assign))
        if unknown:
            sys.exit(f"錯誤：修正清單含未知題號 {unknown[:5]}")
        for src, a in patch.items():
            assign[src] = {"topic": a["topic"], "subtopic": a["subtopic"]}
        print(f"套用一致性修正 {len(patch)} 筆")

    errors = []
    for src, a in assign.items():
        tp, sb = a.get("topic"), a.get("subtopic")
        if tp not in valid:
            errors.append(f"{src}: topic「{tp}」不存在")
        elif sb not in valid[tp]:
            errors.append(f"{src}: subtopic「{sb}」不屬於 topic「{tp}」")

    all_sources = []
    for qf in sorted(QDIR.glob("*.json")):
        for q in json.loads(qf.read_text(encoding="utf-8"))["questions"]:
            all_sources.append(q["source"])
    missing = sorted(set(all_sources) - set(assign))
    extra = sorted(set(assign) - set(all_sources))
    if missing:
        errors.append(f"缺少 {len(missing)} 題指派，例如 {missing[:5]}")
    if extra:
        errors.append(f"多出 {len(extra)} 筆不存在的題號，例如 {extra[:5]}")

    if errors:
        print(f"\n發現 {len(errors)} 個問題，未套用：")
        for e in errors[:30]:
            print(f"  - {e}")
        sys.exit(1)

    # 分布統計
    tc = Counter(a["topic"] for a in assign.values())
    sc = Counter((a["topic"], a["subtopic"]) for a in assign.values())
    print("\n各大類題數：")
    for tp, n in tc.most_common():
        print(f"  {n:>4}  {names[tp]}")
    empty = [sub_names[k] for tp in valid for k in [(tp, s) for s in valid[tp]] if sc[k] == 0]
    if empty:
        print(f"\n無題目的子題 {len(empty)}：{'、'.join(empty)}")

    if dry:
        print("\n（dry-run，未寫檔）")
        return

    for qf in sorted(QDIR.glob("*.json")):
        data = json.loads(qf.read_text(encoding="utf-8"))
        for q in data["questions"]:
            a = assign[q["source"]]
            if "category" in q and "legacy_category" not in q:
                q["legacy_category"] = q.pop("category")
            elif "category" in q:
                q.pop("category")
            q["topic"] = a["topic"]
            q["subtopic"] = a["subtopic"]
        qf.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"寫回 {qf.name}")
    print("\n完成。")


if __name__ == "__main__":
    main()
