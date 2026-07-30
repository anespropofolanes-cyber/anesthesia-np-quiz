#!/usr/bin/env python3
"""依 audit/verification_report.md 第 3-2 節的裁決，把題幹／選項還原成 PDF 原文。

使用者裁決（2026-07-30）：一律與原考題一致。
另依專業判斷，把題庫自行加上的圖說註解從 question 移到新欄位 editor_note，
使 question 純為考題原文，註解由前端以「編註」樣式另外呈現。

本腳本為一次性修正，執行後 compare_with_pdf.py 的「用字不同／題庫省略」應歸零。
以精確字串比對後替換；若原文不符即中止，不會盲改。
"""
import json
import sys
from pathlib import Path

QDIR = Path(__file__).resolve().parent.parent / "data" / "questions"

# (檔名, 題號, 欄位, 原字串, 新字串)　欄位為 "question" 或 "options.X"
FIXES = [
    # ── 題意還原（最重要）：PDF 原文為「最不可能」──
    ("110_advanced", 71, "question",
     "下列鑑別診斷何者較不適當？",
     "下列鑑別診斷何者最不可能？"),

    # ── 補回 PDF 原有的正常參考值（判讀腦脊髓液所必需）──
    ("113_advanced", 7, "question",
     "壓力280mmH2O、白血球計數10000/mm3且以多核球為主、葡萄糖20mg/dL、蛋白質180mg/dL、血糖值正常",
     "壓力280mmH2O（正常參考值70-180mmH2O）、白血球計數10000/mm3且以多核球為主"
     "（正常參考值0-5淋巴球/mm3）、葡萄糖20mg/dL（正常參考值45-85mg/dL）、"
     "蛋白質180mg/dL（正常參考值15-45mg/dL）、血糖值正常"),

    # ── 補回被省略的英文全名／字詞 ──
    ("112_general", 1, "question",
     "世界衛生組織（WHO）在2010年",
     "世界衛生組織（World Health Organization，WHO）在2010年"),
    ("113_advanced", 24, "options.A",
     "COHb 10%",
     "COHb（carboxyhemoglobin）10%"),
    ("110_general", 78, "question",
     "急救過程心電圖呈現竇性心搏過速，抽血結果",
     "急救過程心電圖呈現竇性心搏過速（sinus tachycardia），抽血結果"),
    ("110_advanced", 73, "question",
     "顯示circuit leak漏氣，加大fresh gas flow",
     "顯示circuit leak漏氣，但加大fresh gas flow"),
    ("111_advanced", 80, "options.A",
     "壓脈帶量測血壓",
     "壓脈帶量測血壓即可"),
]

# (檔名, 題號, 要從 question 末尾移除並改放 editor_note 的字串)
NOTE_MOVES = [
    ("113_advanced", 2, "（圖示四種心電圖波形）"),
    ("113_advanced", 65, "（圖示四種擺位方式）"),
    ("113_general", 61,
     "（圖中A=最突出頸椎棘突，B=肩胛骨下角，C=髂嵴上緣（Tuffier line），D=髂後上棘）"),
]


def get_q(data, qid):
    for q in data["questions"]:
        if q["id"] == qid:
            return q
    sys.exit(f"錯誤：找不到 Q{qid}")


def main():
    changed = {}
    errors = []

    for fname, qid, field, old, new in FIXES:
        data = changed.setdefault(fname, json.loads((QDIR / f"{fname}.json").read_text("utf-8")))
        q = get_q(data, qid)
        if field == "question":
            target, key = q, "question"
        else:
            target, key = q["options"], field.split(".", 1)[1]
        if old not in target[key]:
            errors.append(f"{fname} Q{qid} {field}: 找不到原字串「{old}」")
            continue
        target[key] = target[key].replace(old, new, 1)
        print(f"修正 {fname} Q{qid} {field}")

    for fname, qid, note in NOTE_MOVES:
        data = changed.setdefault(fname, json.loads((QDIR / f"{fname}.json").read_text("utf-8")))
        q = get_q(data, qid)
        if note not in q["question"]:
            errors.append(f"{fname} Q{qid}: 找不到圖說註解「{note}」")
            continue
        q["question"] = q["question"].replace(note, "", 1).strip()
        q["editor_note"] = note.strip("（）")
        print(f"移出編註 {fname} Q{qid}")

    if errors:
        print("\n未套用任何變更，錯誤如下：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    for fname, data in changed.items():
        path = QDIR / f"{fname}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"寫回 {path.name}")
    print(f"\n完成：{len(FIXES)} 項還原、{len(NOTE_MOVES)} 項編註分離，共動到 {len(changed)} 個檔。")


if __name__ == "__main__":
    main()
