/* views.js — 畫面渲染 */

const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/** 教材允許 **粗體**，其餘一律逸出。 */
const rich = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

/** 收合狀態的摘要：去掉粗體標記再截斷，避免切在標記中間露出 **。 */
function teaser(s, n = 40) {
  const plain = String(s ?? '').replace(/\*\*/g, '').trim();
  return esc(plain.length > n ? plain.slice(0, n) + '…' : plain);
}

const SUBJ_SHORT = { advanced: '進階', general: '通論' };

function qTags(q, { showTopic = true } = {}) {
  const t = [];
  if (q.note) t.push('<span class="tag note">疑義</span>');
  if (q.disputed) t.push('<span class="tag disputed">答案有爭議</span>');
  if (isFree(q)) t.push('<span class="tag free">送分</span>');
  else if (isMulti(q)) t.push(`<span class="tag multi">多答案 ${esc(q.answer)}</span>`);
  if (showTopic && q.topic) t.push(`<span class="tag topic">${esc(DB.subName[q.subtopic] || DB.topicName[q.topic])}</span>`);
  return t.join('');
}

/* ══ 答題畫面 ══ */
function renderQuiz() {
  const q = curQ(), n = Q.list.length, pick0 = Q.picks[q.source];
  const answered = Object.keys(Q.picks).length;
  const reveal = Q.mode === 'practice' && !!pick0;

  document.getElementById('quiz-head').innerHTML = `
    <div class="progress">
      <span>${esc(Q.label)}</span>
      <span class="bar"><i style="width:${(Q.i + 1) / n * 100}%"></i></span>
      <span>${Q.i + 1} / ${n}</span>
    </div>
    ${Q.mode === 'exam' ? `<div class="dots">${Q.list.map((x, i) =>
      `<button class="dot ${Q.picks[x.source] ? 'done' : ''} ${i === Q.i ? 'cur' : ''}"
        onclick="jump(${i})" aria-label="第 ${i + 1} 題">${i + 1}</button>`).join('')}</div>` : ''}`;

  const opts = ['A', 'B', 'C', 'D'].map(L => {
    let cls = '';
    if (reveal) {
      if (!isFree(q) && q.answer.includes(L)) cls = 'correct';
      else if (pick0 === L) cls = 'wrong';
    } else if (pick0 === L) cls = 'picked';
    return `<li><button class="opt ${cls}" onclick="pick('${L}')" ${reveal ? 'disabled' : ''}>
      <span class="L">${L}</span><span>${esc(q.options[L])}</span></button></li>`;
  }).join('');

  let after = '';
  if (reveal) {
    const ok = isCorrect(q, pick0);
    const v = isFree(q)
      ? '<div class="verdict free">本題送分，全體給分</div>'
      : `<div class="verdict ${ok ? 'ok' : 'no'}">${ok ? '答對了' : `答錯了　正解 ${esc(answerText(q))}`}</div>`;
    after = v + explainHTML(q);
  }

  document.getElementById('quiz-body').innerHTML = `
    <div class="qcard">
      <div class="qhead">
        <span class="qno">${q.year} ${SUBJ_SHORT[q.subject]} Q${q.id}</span>
        ${qTags(q)}
        <button class="iconbtn ${store.isMarked(q.source) ? 'on' : ''}" onclick="toggleMark('${q.source}')"
          title="書籤" aria-label="加入書籤">★</button>
      </div>
      <div class="stem">${esc(q.question)}</div>
      ${q.editor_note ? `<p class="enote">編註：${esc(q.editor_note)}</p>` : ''}
      ${figHTML(q)}
      <ul class="opts">${opts}</ul>
      ${after}
      ${noteHTML(q)}
    </div>`;

  document.getElementById('btn-prev').disabled = Q.i === 0;
  document.getElementById('btn-next').disabled = Q.i === n - 1;
  document.getElementById('btn-finish').textContent =
    Q.mode === 'exam' ? `完成作答並計分（已答 ${answered}／${n}）` : '結束並看成績';
}

function figHTML(q) {
  if (!q.image) return '';
  return `<div class="fig">
    <img src="images/${esc(q.image)}" alt="${esc(q.image_caption || '題目附圖')}"
      loading="lazy" onclick="openLightbox(this.src)" onerror="this.parentNode.style.display='none'">
    ${q.image_caption ? `<div class="cap">${esc(q.image_caption)}</div>` : ''}
  </div>`;
}

function explainHTML(q) {
  return `<div class="explain"><span class="h">解析</span>${esc(q.explanation)}${
    q.review_note ? `<div class="revnote">${esc(q.review_note)}</div>` : ''}</div>`;
}

function noteHTML(q) {
  return `<div class="noteblk">
    <div class="lbl">我的筆記 <span class="saved" id="saved-${esc(q.source)}">已儲存</span></div>
    <textarea placeholder="寫下你自己的理解、記憶法或補充…"
      oninput="onNote('${q.source}', this.value)">${esc(store.getNote(q.source))}</textarea>
  </div>`;
}

let noteTimer = null;
function onNote(src, val) {
  store.setNote(src, val);
  clearTimeout(noteTimer);
  const el = document.getElementById('saved-' + src);
  if (el) { el.classList.add('show'); noteTimer = setTimeout(() => el.classList.remove('show'), 1400); }
  refreshCounts();
}

/* ══ 結果 ══ */
function renderResult() {
  const s = scoreOf();
  const wrongs = Q.list.filter(q => { const p = Q.picks[q.source]; return p && !isCorrect(q, p); });
  const blanks = Q.list.filter(q => !Q.picks[q.source] && !isFree(q));
  const pass = s.pct >= 60;

  document.getElementById('result-body').innerHTML = `
    <h1 class="page">${pass ? '完成，表現不錯' : '完成，還有進步空間'}</h1>
    <p class="lede">${esc(Q.label)}</p>
    <div class="card">
      <div class="score">
        <div class="ring" style="--pct:${s.pct}"><div class="v"><b>${s.pct}%</b><s>正確率</s></div></div>
        <div class="stats">
          <div class="stat ok"><b>${s.ok}</b><s>答對</s></div>
          <div class="stat no"><b>${s.no}</b><s>答錯</s></div>
          <div class="stat"><b>${s.blank}</b><s>未作答</s></div>
        </div>
      </div>
      <div class="btnrow">
        <button class="btn primary" onclick="go('${Q.origin}')">回上一頁</button>
        ${wrongs.length ? `<button class="btn" onclick="practiceSources(${JSON.stringify(wrongs.map(q => q.source)).replace(/"/g, '&quot;')}, '本次錯題複習')">複習本次錯題（${wrongs.length}）</button>` : ''}
        <button class="btn" onclick="startQuiz(Q.list,{mode:Q.mode,label:Q.label,origin:Q.origin})">再做一次</button>
      </div>
    </div>
    ${wrongs.length || blanks.length ? `
      <div class="sect-label">逐題檢討</div>
      <div class="list">${[...wrongs, ...blanks].map(q => reviewItem(q, Q.picks[q.source])).join('')}</div>` : ''}`;
}

function reviewItem(q, my) {
  return `<div class="item">
    <div class="top">
      <strong>${q.year} ${SUBJ_SHORT[q.subject]} Q${q.id}</strong>${qTags(q)}
    </div>
    <div class="q">${esc(q.question)}</div>
    ${figHTML(q)}
    <div class="ans">你的答案：<strong>${my ? `${my}　${esc(q.options[my] || '')}` : '未作答'}</strong><br>
      正解：<strong>${esc(answerText(q))}</strong>${
        isFree(q) ? '' : `　${esc(q.options[q.answer[0]] || '')}`}</div>
    ${explainHTML(q)}
  </div>`;
}

/* ══ 主題總覽 ══ */
function renderTopics() {
  const el = document.getElementById('topic-list');
  const secs = DB.taxonomy.sections.map(sec => {
    const cards = DB.taxonomy.topics.filter(t => t.section === sec.id).map(t => {
      const qs = byTopic(t.id);
      const done = qs.filter(q => store.s.right[q.source]).length;
      const pct = qs.length ? Math.round(done / qs.length * 100) : 0;
      return `<button class="topic" onclick="openTopic('${t.id}')">
        <span class="t">${esc(t.name)}</span>
        <span class="s">${esc(t.summary)}</span>
        <span class="meta"><span>${qs.length} 題</span>
          <span class="bar"><i style="width:${pct}%"></i></span><span>${pct}%</span></span>
      </button>`;
    }).join('');
    return `<div class="sect-label">${esc(sec.name)}　${esc(sec.note)}</div><div class="topics">${cards}</div>`;
  }).join('');
  el.innerHTML = secs;
}

/* ══ 單一主題 ══ */
async function openTopic(topicId) {
  go('topic');
  const t = DB.taxonomy.topics.find(x => x.id === topicId);
  const qs = byTopic(topicId);
  const el = document.getElementById('topic-detail');
  el.innerHTML = `<h1 class="page">${esc(t.name)}</h1>
    <p class="lede">${esc(t.summary)}　共 ${qs.length} 題</p>
    <div class="btnrow" style="margin-bottom:18px">
      <button class="btn primary" onclick="practiceSources(${JSON.stringify(qs.map(q => q.source)).replace(/"/g, '&quot;')}, '${esc(t.name)}', 'topic', true)">
        練習全部 ${qs.length} 題（隨機順序）</button>
    </div>
    <div id="concept-slot"><p class="hint">載入重點觀念…</p></div>
    <div class="sect-label">子題</div>
    <div class="list">${t.subtopics.map(s => {
      const sq = qs.filter(q => q.subtopic === s.id);
      const done = sq.filter(q => store.s.right[q.source]).length;
      return `<button class="item" onclick="practiceSources(${JSON.stringify(sq.map(q => q.source)).replace(/"/g, '&quot;')}, '${esc(t.name)}／${esc(s.name)}', 'topic', true)"
        ${sq.length ? '' : 'disabled style="opacity:.5"'}>
        <div class="top"><strong>${esc(s.name)}</strong>
          <span class="tag">${sq.length} 題</span>
          ${done ? `<span class="tag topic">已答對 ${done}</span>` : ''}</div>
        <div class="ans">${esc(s.note)}</div>
      </button>`;
    }).join('')}</div>`;

  const c = await loadConcept(topicId);
  document.getElementById('concept-slot').innerHTML = c ? conceptHTML(c) :
    `<div class="card"><h2>重點觀念</h2><p class="hint" style="margin:0">這個主題的教材還在整理中。可以先從下方的子題開始練習。</p></div>`;
}

/** 教材每章 800–2300 字，全部展開會有近萬像素的捲動長度，
    故各章預設收合，由讀者自己決定要看哪一段。 */
function conceptHTML(c) {
  const secs = c.sections || [];
  return `<div class="card concept">
    <div class="chead">
      <h2>重點觀念</h2>
      <button class="btn sm" id="btn-expand" onclick="toggleAllSections()">全部展開</button>
    </div>
    ${c.intro ? `<p class="cintro">${rich(c.intro)}</p>` : ''}
    ${secs.map((s, i) => `
      <details class="csec" ${i === 0 ? 'open' : ''}>
        <summary>
          <span class="ct">${esc(s.title)}</span>
          <span class="cf">${teaser(s.exam_focus)}</span>
        </summary>
        <div class="cbody">
          ${s.exam_focus ? `<div class="focus">歷屆考點：${rich(s.exam_focus)}</div>` : ''}
          ${(s.blocks || []).map(blockHTML).join('')}
          ${(s.question_refs || []).length ? `
            <button class="btn sm" onclick="practiceSources(${JSON.stringify(s.question_refs).replace(/"/g, '&quot;')}, '${esc(c.title)}／${esc(s.title)}', 'topic')">
              練這一段的代表題（${s.question_refs.length}）</button>` : ''}
        </div>
      </details>`).join('')}
  </div>`;
}

function toggleAllSections() {
  const all = [...document.querySelectorAll('.csec')];
  const anyClosed = all.some(d => !d.open);
  all.forEach(d => { d.open = anyClosed; });
  document.getElementById('btn-expand').textContent = anyClosed ? '全部收合' : '全部展開';
}

function blockHTML(b) {
  const head = b.heading ? `<div class="bh">${esc(b.heading)}</div>` : '';
  if (b.type === 'table') {
    return `<div class="blk">${head}<div class="tblwrap"><table class="ct">
      <thead><tr>${(b.columns || []).map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
      <tbody>${(b.rows || []).map(r => `<tr>${r.map(c => `<td>${rich(c)}</td>`).join('')}</tr>`).join('')}</tbody>
    </table></div></div>`;
  }
  if (b.type === 'compare') {
    return `<div class="blk">${head}<div class="cmp">${(b.items || []).map(i =>
      `<div class="row"><div class="pair">${esc(i.a)}<em>vs</em>${esc(i.b)}</div><div>${rich(i.note)}</div></div>`).join('')}</div></div>`;
  }
  const cls = b.type === 'pitfall' ? 'blk pitfall' : 'blk';
  return `<div class="${cls}">${head}<p>${rich(b.content)}</p></div>`;
}

/* ══ 清單頁 ══ */
function renderList(kind) {
  const map = { wrong: 'wrong-list', mark: 'mark-list', note: 'note-list' }[kind];
  const el = document.getElementById(map);
  const keys = Object.keys(kind === 'wrong' ? store.s.wrong : kind === 'mark' ? store.s.marks : store.s.notes);
  const items = keys.map(s => DB.index[s]).filter(Boolean);
  if (!items.length) {
    const msg = { wrong: '還沒有錯題。開始練習後答錯的題目會自動收進來。',
                  mark: '還沒有書籤。在答題畫面點右上角的星號即可標記。',
                  note: '還沒有筆記。在任何一題下方的筆記欄寫下想法即可。' }[kind];
    el.innerHTML = `<div class="empty"><div class="big">·</div>${msg}</div>`;
    return;
  }
  items.sort((a, b) => {
    const t = kind === 'wrong' ? store.s.wrong : kind === 'mark' ? store.s.marks : store.s.notes;
    return (t[b.source].at || 0) - (t[a.source].at || 0);
  });
  el.innerHTML = `<div class="list">${items.map(q => {
    const extra = kind === 'wrong'
      ? `<div class="ans">你答過：<strong>${esc(store.s.wrong[q.source].my || '—')}</strong>　正解：<strong>${esc(answerText(q))}</strong>　答錯 ${store.s.wrong[q.source].n} 次</div>`
      : kind === 'note'
        ? `<div class="explain" style="margin-top:10px"><span class="h">我的筆記</span>${esc(store.getNote(q.source))}</div>`
        : `<div class="ans">正解：<strong>${esc(answerText(q))}</strong></div>`;
    return `<div class="item">
      <div class="top"><strong>${q.year} ${SUBJ_SHORT[q.subject]} Q${q.id}</strong>${qTags(q)}
        <button class="btn sm" style="margin-left:auto" onclick="practiceSources(['${q.source}'],'單題複習')">練這題</button></div>
      <div class="q">${esc(q.question)}</div>${extra}
      ${kind !== 'note' ? explainHTML(q) : ''}
      <div class="btnrow" style="margin-top:10px">
        ${kind === 'wrong' ? `<button class="btn sm" onclick="store.clearWrong('${q.source}');renderList('wrong');refreshCounts()">從錯題本移除</button>` : ''}
        ${kind === 'mark' ? `<button class="btn sm" onclick="toggleMark('${q.source}');renderList('mark')">取消書籤</button>` : ''}
      </div>
    </div>`;
  }).join('')}</div>`;
}

/* ══ 搜尋 ══ */
function doSearch() {
  const kw = document.getElementById('q').value.trim();
  const el = document.getElementById('search-result');
  if (kw.length < 2) { el.innerHTML = `<p class="hint">請輸入至少 2 個字。</p>`; return; }
  const lc = kw.toLowerCase();
  const hits = allQuestions().filter(q =>
    q.question.toLowerCase().includes(lc) ||
    q.explanation.toLowerCase().includes(lc) ||
    Object.values(q.options).some(o => o.toLowerCase().includes(lc))
  ).slice(0, 60);
  if (!hits.length) { el.innerHTML = `<div class="empty">找不到含「${esc(kw)}」的題目。</div>`; return; }
  const hl = s => esc(s).replace(new RegExp(esc(kw).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), m => `<mark>${m}</mark>`);
  el.innerHTML = `<p class="hint">找到 ${hits.length} 題${hits.length === 60 ? '（僅顯示前 60 題）' : ''}</p>
    <div class="btnrow" style="margin-bottom:14px">
      <button class="btn sm" onclick="practiceSources(${JSON.stringify(hits.map(q => q.source)).replace(/"/g, '&quot;')}, '搜尋：${esc(kw)}')">練習這 ${hits.length} 題</button>
    </div>
    <div class="list">${hits.map(q => `<div class="item">
      <div class="top"><strong>${q.year} ${SUBJ_SHORT[q.subject]} Q${q.id}</strong>${qTags(q)}
        <button class="btn sm" style="margin-left:auto" onclick="practiceSources(['${q.source}'],'單題練習')">練這題</button></div>
      <div class="q">${hl(q.question)}</div>
      <div class="ans">正解：<strong>${esc(answerText(q))}</strong></div>
    </div>`).join('')}</div>`;
}
