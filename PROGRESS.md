# 麻醉護理考題解析 PWA — 進度追蹤

> 新對話開工前先讀本檔。完整計畫見各 Phase 說明；原始題庫（唯讀）在
> `/Users/huangxinyi/Documents/Claude/Projects/專科護理師題庫/`。

## 專案總覽

- 目標：獨立的麻醉專科護理師題庫 PWA，部署 GitHub Pages
- 資料：109–114 年 × 進階/通論 = 960 題（`data/questions/*.json`）
- 兩模式：歷屆試題（功能對齊舊版＋修 bug）＋ 主題學習（11 大類臨床邏輯）
- 內建重點觀念教材（Claude 起草、使用者修訂）＋ 個人筆記（localStorage＋匯出）

## 進度

| Phase | 內容 | 狀態 |
|---|---|---|
| 0 | 資料抽取＋驗證腳本＋圖片 | ✅ 2026-07-30 完成 |
| 1a | PDF↔題庫文字/答案比對 | ✅ 完成（7 項已修正） |
| 1b | 校對版 PDF ✅／解析審查 ✅／圖檔重做 ✅ | ✅ 完成 |
| 2 | 重新分類（taxonomy） | ✅ 2026-07-30 完成 |
| 3 | 重點觀念教材初稿 | 12/13 主題完成（health_promotion 進行中） |
| 4 | PWA 建置 | ✅ 完成並實測通過 |
| 5 | GitHub Pages 部署 | 待辦 |

## Phase 0 記錄（2026-07-30）

- `tools/extract_from_html.py`：從舊 HTML 抽 12 區塊 → `data/questions/<year>_<subject>.json`
- `tools/validate_questions.py`：結構驗證，**全部通過**（12 檔 × 80 題）
- **命名統一**：舊專案 111–114 進階科 source/image 用 `_anesthesia_` 前綴，已全部改為
  `_advanced_`（source 欄位＋圖檔名皆改）；圖檔清掉 15 個 `_preview_/_render_/_tmp_` 暫存檔，
  剩 31 張，與 31 題圖片題一一對應
- 特殊題（與舊 audit_log 一致）：
  - 送分 7 題：111_general_Q24、112_general_Q46/Q60/Q80、113_advanced_Q33/Q59、113_general_Q68
  - 多答案 15 題（BC/AC/BCD/AB/ABC/ACD/BD/CD 等，見 validate 輸出）
  - 疑義 note 5 題：109_advanced_Q31/Q32、110_general_Q27/Q40/Q43

## Phase 1a 記錄（2026-07-30）

- `tools/parse_pdf.py`：12 份試題 PDF 全部重抽 80 題（補齊舊專案缺的 111 通論、114 兩科）
  - 113_advanced.pdf 第 3 頁是 Q1 重複殘留頁，抽取器自動跳過
- `tools/compare_with_pdf.py`：正規化＋子序列分類比對，報告 `audit/compare_report.md`
- 完整報告：`audit/verification_report.md`
- 結果：結構全通過；22 題疑義公告答案全對（答案卡核對見下方⭐節）
- 7 項差異已全部依原考題修正（見 Phase 1b）
- 另待確認：112_general Q46「送分」查無公告來源
- 110 年掉字已用**字元座標法**驗證完畢（`get_texttrace()` 還原空隙寬度→推定缺字）：
  29 處中 27 處題庫正確、1 處為原卷拼字錯誤（larygospasm）、
  1 處標點位置不同（110_general Q78，待使用者決定）
  ※ 110 年 PDF 是子集字型字形遺失，**紙面上就是空白**，看圖也讀不出來

## Phase 1b 記錄（2026-07-30）

- 7 項題幹差異已依使用者裁決全部還原成原考題（`tools/apply_fixes_20260730.py`）
- 3 題題庫自加的圖說註解移到新欄位 `editor_note`，question 保持純原文
- `tools/make_proof_pdf.py`：HTML → Chrome headless 印 PDF，產出 `proof/` 7 份約 340 頁
  - 每年一份（160 題，3 題／頁）＋ 特殊題清單（含 31 張圖片題總覽供檢查圖質）
- **9 張問題圖檔已全部重做**（原為頁面截圖，含題幹文字／衛福部浮水印；
  110_general_Q73 一張圖混了 Q73＋Q74）。作法：在記憶體中移除 PDF 浮水印物件後
  400 dpi 精確 clip 算繪，解析度提升 2 倍以上。舊檔備份於 `images_backup_20260730/`
- 960 題解析醫學審查：6 組子代理平行進行中

## ⭐ 官方答案卡核對（2026-07-30，重大進展）

使用者提供 `專科考試.zip`（GoodNotes），從 `.goodnotes`（zip 格式）的 `attachments/`
抽出 10 份官方標準答案卡 → `source/answer_keys/`。工具 `tools/verify_answer_keys.py`。

- **12 卷 960 題全部核對完成**（GoodNotes 內嵌 10 份 ＋ 使用者另提供 114 兩份）
- **發現 1 題答案錯誤並更正**：`109_general Q72` D → B
  （官方答案 B；原解析誤把 ST 段抬高判讀成高血鉀高尖 T 波，且誤植了 Q53 的洗腎病史）
- **更正後 960 題答案 100% 與官方一致**
- 114 答案卡為不同的 8 欄配對佈局，已兩法交叉驗證＋目視確認

## 解析醫學審查與修訂（2026-07-30）── ✅ 59 題全部修訂完成

960 題中 59 題解析有醫學問題（高 5、中 30、低 24），報告在
`audit/explanation_review/README.md`。**已全部修訂完畢**，每題加 `review_note` 記錄原本錯在哪。

修訂分工：主對話 14 題（5 高嚴重度＋9 自相矛盾）＋ 三組子代理 45 題（依年份分工避免檔案衝突）。
修訂後 `validate_questions.py` 與 `verify_answer_keys.py` 皆通過，
`answer`／`question`／`options` 全程未動。

**最重要的系統性問題**：多題解析推理走不到官方答案時，用「依公告答案為 X」或「可能……」
蓋過缺口，造成解析自相矛盾——而查證後官方答案幾乎都是對的，是解析算錯或漏掉關鍵判準。
修訂原則因此定為：**解析必須自己走得到答案**；真有爭議則明說爭議點。

發現 3 題**題目／答案本身有瑕疵**，已在解析中明白標註而非硬套：
- `112_advanced_Q15`（大量血胸，選項 B 依 ATLS 其實正確）→ 另加 `disputed` 欄位
- `110_general_Q25`（代謝症候群，四選項無一達 3 項）
- `109_advanced_Q50`（MAC，選項 C 在多數教科書屬可接受敘述）

## Phase 2 分類架構（2026-07-30 定案）

`data/taxonomy.json` v1.1：**兩區塊 → 13 大類 → 84 子題**

- 【麻醉專業】麻醉藥理學／麻醉相關生理與解剖／術前評估與準備／氣道管理／監測與麻醉設備／
  全身麻醉照護／區域麻醉與疼痛管理／特殊病人族群麻醉／各專科手術麻醉／危機處理與併發症
- 【護理專業】一般臨床醫學與照護／健康促進與病人教育／專業實務、倫理與法規

使用者裁決（2026-07-30）：
1. 原「特殊族群與專科手術麻醉」12 子題過大 → **拆成「特殊病人族群麻醉」（病人特性）
   與「各專科手術麻醉」（術式特性）**
2. 疼痛管理**維持**與區域麻醉合併
3. 心電圖判讀**維持**置於「監測與麻醉設備」下

歸類流程：6 組子代理（各一年 160 題）→ `audit/taxonomy_assign/<年>.json`
→ 一致性覆核代理 → `_consistency_patch.json` → `tools/apply_taxonomy.py` 集中驗證後套用。
**已完成**：960 題皆有 topic/subtopic，原 `category` 存為 `legacy_category`。
分布報告見 `audit/taxonomy_distribution.md`。

架構最終為 **v1.5：13 大類、87 子題、16 條邊界判準**。歸類過程中補了三個缺口
（`crisis/or_fire` 手術室火災、`specialty_surgery/vascular` 血管手術、`ga_care/eras`），
一致性覆核修正 23 題——其中最嚴重的是 **ERAS 的 8 題原本散在 5 個不同落點**，
以及 6 題手術室火災全躺在耳鼻喉眼牙科下。

主對話裁決的 4 項爭議（已寫入 boundary_rules）：
1. 剖腹產 ERAS 有明確產科落點 → 維持 `special_patient/obstetric`
2. POVL 是體位傷害的核心概念，四題集中 → 全歸 `ga_care/positioning`
3. `114_advanced_Q68` 正解考 cefazolin 抗菌譜 → `clinical_medicine/infectious_dz`
   （手部衛生等純感控才歸 patient_safety）
4. RSI 選藥與誘導技術不可分，三題統一 → `ga_care/induction`

## Phase 4 記錄（2026-07-30）

PWA 已建置完成並在本機實測通過。純 vanilla JS、無框架、無建置流程。

檔案：`index.html`／`css/app.css`／`js/{store,data,quiz,views,app}.js`／`sw.js`／
`manifest.webmanifest`／`icons/`（由舊專案 icon.png 產生，含 maskable）

**已驗證的功能**
- 歷屆試題（年份×科目×主題×難度篩選、練習／考試兩模式、隨機出題）
- 主題學習（13 大類卡片＋進度、子題練習、重點觀念教材渲染）
- **送分題與多答案判定正確**（舊版的送分永遠判錯已修好，實測 `isCorrect` 全部通過）
- 錯題本／書籤／個人筆記／匯出匯入／全文搜尋／字級三段／圖片 lightbox
- 深色模式、行動版無水平溢出（375px 實測）
- **離線實測通過**：關閉本機伺服器後重新載入，960 題完整可用

**離線快取的設計決定**
- 核心資源（題目＋教材＋程式，約 1.2MB）由**頁面端**的 `ensureOfflineCore()` 確保入快取，
  不倚賴 service worker 的 install 時機——實測發現使用者清過瀏覽器資料而 sw.js 未改版時，
  install 不會重跑，快取補不回來
- `fetch` 一律帶 `cache: 'reload'` 繞過瀏覽器 HTTP 快取，避免存到舊檔（實測踩過這個坑）
- **圖檔 13MB 不自動下載**，在「備份與匯出」頁提供按鈕由使用者決定何時抓，
  以免耗用他人行動網路

**圖片最佳化**：31 張從 17.9MB 壓到 12.9MB（上限 1400px），目視確認畫質無損

**教材頁面過長的處理**：各主題教材 9–22K 字元，全部展開會有近 2 萬像素的捲動長度。
改為各章 `<details>` 收合（首章展開）＋「全部展開」切換，
specialty_surgery 頁從 19,622px 降到 4,678px。每章底部另有「練這一段的代表題」按鈕。

**改版流程（三處要同步，否則使用者拿到新舊混雜的檔案）**
1. `index.html` 的 `?v=` → 2. `sw.js` 的 `ASSET_V` → 3. `sw.js` 的 `VERSION` 加一
（`js/app.js` 的 `CACHE_NAME` 必須與 `sw.js` 的 `CACHE` 一致）
目前版本：ASSET_V `20260731a`／CACHE `anes-np-v2`

## 設計配色（使用者指定 2026-07-30）

- `#f2dbe1` 粉：主色（標題底、正解highlight）
- `#9ac5cd` 藍綠：輔色（強調線、編註框）
- `#fcf4d7` 奶油：底色（解析區、資訊框）

## 已知需修正（新 PWA）

1. 舊版「送分」題永遠判錯（`isCorrect` 用 split('') 比對）→ 新版送分一律計對＋徽章
2. 考試模式 progress-score 殘留 → 新版重寫
3. 新版為公開站，**不設密碼門**

## 慣例

- `q.image` 一律裸檔名，renderer 自行加 `images/` 前綴
- answer：`"A"`／多答案 `"BC"`（遞增排序）／`"送分"`
- 舊專案目錄只讀不寫
