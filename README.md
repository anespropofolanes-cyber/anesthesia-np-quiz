# 麻醉專科護理師題庫

**線上使用**：<https://anespropofolanes-cyber.github.io/anesthesia-np-quiz/>

衛生福利部麻醉專科護理師甄審歷屆試題（109–114 年，共 960 題）的線上練習網站。
可安裝成手機 App（PWA），離線也能用。

## 這份題庫做過什麼查核

| 項目 | 結果 |
|---|---|
| 答案 | **12 卷 960 題全部與衛生福利部官方標準答案卡逐題核對**，找到並更正 1 題錯誤（109 通論 Q72） |
| 疑義公告 | 送分 7 題、多答案 15 題，逐一對照 8 份衛福部疑義試題答案公告 |
| 題幹與選項 | 12 份試題 PDF 全部重新抽取比對；110 年 PDF 字形遺失處另以字元座標還原驗證 |
| 解析 | 960 題逐題醫學審查，修訂 59 題（含 5 題高嚴重度，如 sugammadex 劑量、ACLS 去顫能量） |
| 圖片 | 31 張，其中 9 張重新製作（原為頁面截圖，含題幹文字或衛福部浮水印） |

詳細報告在 [`audit/`](audit/)：

- [`verification_report.md`](audit/verification_report.md) — 全面驗證報告
- [`compare_report.md`](audit/compare_report.md) — 題庫與 PDF 原文的逐項差異
- [`explanation_review/README.md`](audit/explanation_review/README.md) — 解析醫學審查
- [`taxonomy_distribution.md`](audit/taxonomy_distribution.md) — 主題分類分布

## 功能

- **歷屆試題** — 依年份與科目整卷練習，可再依主題或難度篩選。練習模式即時看解析，模擬考試最後統一計分
- **主題學習** — 依臨床學習邏輯分成 13 大類、87 子題。每個主題有從歷屆考題歸納的重點觀念，可跨年度練該主題的題目
- **錯題本／書籤／個人筆記** — 全部存在自己的瀏覽器裡，不上傳。可匯出 JSON 備份
- **搜尋** — 題幹、選項、解析全文檢索
- **離線可用** — 題目與教材自動快取；圖檔約 13 MB，由使用者在「備份與匯出」頁主動下載

## 開發

純 vanilla JS，沒有框架也沒有建置流程。用任何靜態伺服器打開即可：

```bash
python3 -m http.server 8899
```

然後開 <http://localhost:8899>。**不能用檔案總管直接開 `index.html`**，
因為資料是用 `fetch` 載入的，`file://` 通訊協定會被瀏覽器擋下。

### 檔案結構

```
index.html            單頁應用的殼
css/app.css           全部樣式（含深色模式）
js/store.js           localStorage 存取層
js/data.js            題庫載入與答案判定
js/quiz.js            答題流程
js/views.js           畫面渲染
js/app.js             啟動、路由、離線快取
sw.js                 service worker
data/questions/*.json 12 卷題目（每卷 80 題）
data/taxonomy.json    主題分類架構與邊界判準
data/concepts/*.json  各主題的重點觀念教材
images/               31 張題目附圖
source/answer_keys/   12 份官方標準答案卡（查核依據）
tools/                Python 工具：抽取、驗證、比對、產生校對版 PDF
proof/                校對版 PDF（每年一份 ＋ 特殊題清單）
```

### 題目資料格式

```json
{
  "id": 33,
  "question": "題幹",
  "options": { "A": "…", "B": "…", "C": "…", "D": "…" },
  "answer": "B",
  "explanation": "解析",
  "difficulty": "medium",
  "source": "113_advanced_Q33",
  "topic": "regional_pain",
  "subtopic": "neuraxial",
  "legacy_category": "regional",
  "image": "113_advanced_Q33.png",
  "image_caption": "圖說",
  "editor_note": "非考題原文的編註",
  "note": "疑義公告說明",
  "review_note": "修訂紀錄",
  "disputed": "答案有爭議時的說明"
}
```

`answer` 有三種：單一字母 `"B"`、多答案 `"BC"`（任一即給分）、`"送分"`（全體給分）。
`image` **一律是裸檔名**，程式會自動加上 `images/` 前綴。

### 修改題庫後務必執行

```bash
python3 tools/validate_questions.py
python3 tools/verify_answer_keys.py --scan source/answer_keys
```

第二個指令必須顯示「所有可核對的卷別，答案全部與官方一致」。
**答案是這份題庫的核心價值，不要在沒有官方依據的情況下更動。**

### 新增年份

1. 把試題 PDF 與標準答案卡放進 `source/`
2. `python3 tools/parse_pdf.py <pdf> <year> <subject>` 抽出題目
3. 建立 `data/questions/<year>_<subject>.json`，依上述格式填入
4. 依 `data/taxonomy.json` 的 `_meta.boundary_rules`（16 條邊界判準）指派 topic 與 subtopic
5. 更新 `js/data.js` 的 `YEARS` 與 `sw.js` 的 `YEARS`
6. 跑上面兩個驗證指令

### 改版後更新離線快取

編輯 `sw.js` 把 `VERSION` 加一（如 `v1` → `v2`），舊快取會自動清除。

## 授權與免責

題目與答案為衛生福利部歷年公告內容。解析、分類與教材為自行整理，僅供學習參考，
不構成臨床指引。發現錯誤歡迎回報。
