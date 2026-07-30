#!/usr/bin/env python3
"""檢查網站資料夾是否完整——確認每一個被引用到的檔案都真的存在。

用途：擔心上傳漏檔時，跑這個就知道。它會把 index.html、sw.js、題庫 JSON 裡
提到的每個檔案都對一遍，缺一個就會報出來。

用法：
    python3 tools/check_site.py            # 檢查 publish/
    python3 tools/check_site.py <資料夾>    # 檢查指定資料夾
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YEARS = range(109, 115)
SUBJECTS = ("advanced", "general")


def main():
    site = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "publish"
    if not site.is_dir():
        sys.exit(f"找不到資料夾：{site}")

    print(f"檢查 {site}\n")
    missing, checked = [], 0

    def need(rel, why):
        nonlocal checked
        checked += 1
        if not (site / rel).is_file():
            missing.append(f"{rel}　（{why}）")

    # 1. 網站骨架
    for f in ("index.html", "manifest.webmanifest", "sw.js"):
        need(f, "網站必要檔案")

    # 2. index.html 引用的 css / js（含 ?v= 版本參數要剝掉）
    html = (site / "index.html").read_text(encoding="utf-8") if (site / "index.html").is_file() else ""
    for m in re.findall(r'(?:href|src)="((?:css|js|assets|icons)/[^"]+)"', html):
        need(m.split("?")[0], "index.html 有引用")

    # 3. 分類架構與 12 卷題目
    need("data/taxonomy.json", "主題分類架構")
    for y in YEARS:
        for s in SUBJECTS:
            need(f"data/questions/{y}_{s}.json", "題庫")

    # 4. 每個主題的教材
    tax_path = site / "data/taxonomy.json"
    topics = []
    if tax_path.is_file():
        topics = [t["id"] for t in json.loads(tax_path.read_text(encoding="utf-8"))["topics"]]
        for t in topics:
            need(f"data/concepts/{t}.json", "重點觀念教材")

    # 5. 題庫裡每一題引用到的圖
    n_q = n_img = 0
    for y in YEARS:
        for s in SUBJECTS:
            p = site / f"data/questions/{y}_{s}.json"
            if not p.is_file():
                continue
            for q in json.loads(p.read_text(encoding="utf-8"))["questions"]:
                n_q += 1
                if q.get("image"):
                    n_img += 1
                    need(f"images/{q['image']}", f"{q['source']} 的附圖")

    # 6. manifest 裡的圖示
    mp = site / "manifest.webmanifest"
    if mp.is_file():
        for icon in json.loads(mp.read_text(encoding="utf-8")).get("icons", []):
            need(icon["src"], "App 圖示")

    print(f"題目 {n_q} 題　圖片題 {n_img} 題　主題 {len(topics)} 個")
    print(f"共檢查 {checked} 個檔案\n")

    if missing:
        print(f"缺少 {len(missing)} 個檔案：")
        for m in missing:
            print(f"  ✗ {m}")
        print("\n請把上列檔案補上去，網站才會完整。")
        sys.exit(1)

    if n_q != 960:
        print(f"注意：題目總數是 {n_q}，預期 960。可能有題庫檔沒傳完整。")
        sys.exit(1)

    print("完整，沒有缺任何檔案。")


if __name__ == "__main__":
    main()
