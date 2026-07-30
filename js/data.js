/* data.js — 題庫與教材載入
   資料是分離的 JSON，首次用到才 fetch，載入後快取在記憶體。 */

const YEARS = [109, 110, 111, 112, 113, 114];
const SUBJECTS = [
  { id: 'advanced', name: '進階專科護理' },
  { id: 'general', name: '專科護理通論' }
];
const DIFFS = [
  { id: 'easy', name: '初級' },
  { id: 'medium', name: '中級' },
  { id: 'hard', name: '高級' }
];

const DB = {
  taxonomy: null,
  papers: {},     // "113_advanced" -> {meta, questions}
  concepts: {},   // topic -> 教材或 null
  index: null,    // source -> question（全部載入後才有）
  topicName: {}, subName: {}, topicOf: {}
};

async function getJSON(path) {
  const r = await fetch(path, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`載入失敗 ${path}（${r.status}）`);
  return r.json();
}

async function loadTaxonomy() {
  if (DB.taxonomy) return DB.taxonomy;
  const t = await getJSON('data/taxonomy.json');
  DB.taxonomy = t;
  for (const tp of t.topics) {
    DB.topicName[tp.id] = tp.name;
    for (const s of tp.subtopics) {
      DB.subName[s.id] = s.name;
      DB.topicOf[s.id] = tp.id;
    }
  }
  return t;
}

async function loadPaper(year, subject) {
  const key = `${year}_${subject}`;
  if (DB.papers[key]) return DB.papers[key];
  const p = await getJSON(`data/questions/${key}.json`);
  p.questions.forEach(q => { q.year = year; q.subject = subject; });
  DB.papers[key] = p;
  return p;
}

/** 載入全部 12 卷並建立 source 索引。主題學習與搜尋需要。 */
async function loadAll() {
  if (DB.index) return DB.index;
  const jobs = [];
  for (const y of YEARS) for (const s of SUBJECTS) jobs.push(loadPaper(y, s.id));
  await Promise.all(jobs);
  DB.index = {};
  for (const p of Object.values(DB.papers)) {
    for (const q of p.questions) DB.index[q.source] = q;
  }
  return DB.index;
}

function allQuestions() {
  return Object.values(DB.index || {});
}

function byTopic(topicId) {
  return allQuestions().filter(q => q.topic === topicId)
    .sort((a, b) => a.subtopic.localeCompare(b.subtopic) || a.source.localeCompare(b.source));
}

function bySubtopic(subId) {
  return allQuestions().filter(q => q.subtopic === subId);
}

async function loadConcept(topicId) {
  if (topicId in DB.concepts) return DB.concepts[topicId];
  try {
    DB.concepts[topicId] = await getJSON(`data/concepts/${topicId}.json`);
  } catch {
    DB.concepts[topicId] = null;   // 教材尚未撰寫
  }
  return DB.concepts[topicId];
}

/* ── 答案判定 ──
   answer 可能是 "A"、多答案 "BC"（任一即對）、或 "送分"（一律計對）。
   舊版網站用 split('') 比對，導致 7 題送分題永遠判錯——這裡修正。 */
function isFree(q) { return q.answer === '送分'; }
function isMulti(q) { return !isFree(q) && q.answer.length > 1; }
function isCorrect(q, pick) {
  if (isFree(q)) return true;
  return !!pick && q.answer.includes(pick);
}
function answerText(q) {
  if (isFree(q)) return '送分（全題給分）';
  return q.answer.split('').join('、');
}
