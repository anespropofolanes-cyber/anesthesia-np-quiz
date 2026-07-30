#!/usr/bin/env python3
"""解析修訂 第二批：兩題需親自看圖／需標註答案爭議者。

110_advanced Q24：已實際檢視 images/110_advanced_Q24.png 確認心律型態。
112_advanced Q15：官方答案本身有爭議，改為據實說明並標註爭議點。
"""
import json
import sys
from pathlib import Path

QDIR = Path(__file__).resolve().parent.parent / "data" / "questions"
REV = "2026-07-30 解析審查修訂"

FIXES = [
    ("110_advanced", 24, "VF 電擊能量雙相 200J 正確",
     "D 正確：在 CPR 過程中，若電擊無效，amiodarone 首劑 **300 mg IV push**"
     "（第二劑 150 mg）是 VF／無脈搏 VT 的標準抗心律不整用藥（AHA/ACLS 2020）。\n"
     "A 錯誤：圖（一）為**規則、單一形態的寬 QRS 心搏過速**，合併無脈搏 → 屬**無脈搏心室頻脈（pVT）**，"
     "並非心室顫動（VF 的特徵是完全不規則、振幅與形態雜亂、無可辨識的 QRS）。"
     "本題考的正是 pVT 與 VF 的心電圖鑑別——雖然兩者的急救處置相同"
     "（皆需立即非同步去顫，雙相 120–200 J，電擊後立刻恢復壓胸），"
     "但 A 的**心律判讀本身**是錯的。\n"
     "B 錯誤：atropine 用於有脈搏的心搏過緩，對 VF／pVT 無效，已自 ACLS 心跳停止流程中移除。\n"
     "C 錯誤：**無脈搏**的 torsades de pointes 屬心跳停止，MgSO₄ 1–2 g 應稀釋後 **IV push**，"
     "不能 drip 30 分鐘（有脈搏的 torsades 才是 1–2 g 於 15 分鐘內輸注）。",
     "原解析寫「此心電圖為 VF」且稱選項 A 的處置內容正確，卻選 D，前後矛盾。"
     "已實際檢視圖檔確認為規則單型性寬 QRS 心搏過速（pVT），A 錯在心律判讀。"),

    ("112_advanced", 15, "大量血胸頸靜脈應",
     "⚠️ **本題答案有爭議，請留意。**\n"
     "依 ATLS（第 9／10 版胸部創傷章）的標準鑑別："
     "**大量血胸**因大量失血呈低血容狀態，頸靜脈通常**塌陷（flat）**、患側呼吸音降低、"
     "患側叩診呈**實音**；**張力性氣胸**與**心包填塞**才會出現頸靜脈**怒張**，"
     "前者叩診呈鼓音、後者雙側肺音對稱乾淨併心音遙遠（Beck's triad）。\n"
     "因此選項 B 所述「頸靜脈塌陷……叩診實音」與 ATLS 相符；"
     "命題者判 B 為「最不適當」，較可能的著眼點是**氣管偏移並非大量血胸的典型表現**"
     "（氣管偏移主要見於張力性氣胸），而非頸靜脈的描述。\n"
     "【學習重點】請記住 ATLS 的正確鑑別：大量血胸＝頸靜脈**塌陷**＋叩診**實音**；"
     "張力性氣胸＝頸靜脈**怒張**＋叩診**鼓音**＋氣管偏移；心包填塞＝頸靜脈**怒張**＋心音遙遠。"
     "**切勿記成「大量血胸頸靜脈怒張」。**",
     "原解析寫「大量血胸頸靜脈應怒張（非塌陷）」，與 ATLS 標準相反，"
     "會把胸部創傷最核心的鑑別點教錯。已改為據實說明 ATLS 判準並標註本題答案爭議。"),
]


def main():
    changed, errors = {}, []
    for fname, qid, probe, new_exp, reason in FIXES:
        data = changed.setdefault(fname, json.loads((QDIR / f"{fname}.json").read_text("utf-8")))
        q = next((x for x in data["questions"] if x["id"] == qid), None)
        if q is None or probe not in q.get("explanation", ""):
            errors.append(f"{fname} Q{qid}: 找不到題目或原解析不含「{probe}」")
            continue
        q["explanation"] = new_exp
        q["review_note"] = f"{REV}：{reason}"
        if fname == "112_advanced" and qid == 15:
            q["disputed"] = "官方答案 B 依 ATLS 標準有爭議，解析中已說明"
        print(f"修訂 {fname} Q{qid}")

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
