// 키보토스 채팅 프론트엔드. 프레임워크 없이 순수 JS로 작성했다.
"use strict";

const $ = (sel) => document.querySelector(sel);

const state = {
  token: localStorage.getItem("token") || "",
  me: null,
  catalog: null,
  students: {},     // id → 학생
  bonds: {},        // id → {affection, stage, memory}
  rooms: [],
  room: null,       // 열려 있는 채팅방 (메시지 포함)
  schoolFilter: "",
  busy: false,
};

// ───────── 서버 통신 ─────────
async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(state.token && { Authorization: `Bearer ${state.token}` }),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && state.token) logout();
  if (!res.ok) {
    const d = data.detail;
    throw new Error(Array.isArray(d) ? "입력값을 확인하세요." : d || `오류 ${res.status}`);
  }
  return data;
}

function toast(text) {
  const t = $("#toast");
  t.textContent = text;
  t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.hidden = true), 3500);
}

// innerHTML에 넣는 모든 외부 텍스트(특히 AI 응답)는 반드시 이스케이프한다. (XSS 방지)
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// ───────── 공통 조각 ─────────
function schoolOf(st) {
  return state.catalog.schools[st.school] || { name: st.school, color: "#2a9df4" };
}

function halo(st, size = "") {
  const pct = state.bonds[st.id]?.affection ?? 0;
  return `<span class="halo ${size}" data-halo="${esc(st.id)}" style="--school:${schoolOf(st).color};--pct:${pct}">
    <span class="ring"></span><span class="face" aria-hidden="true">${esc(st.name[0])}</span>${artImg(st)}</span>`;
}
// 학생 얼굴: SchaleDB의 공식 아이콘을 링크로만 불러온다. 실패하면 이미지를 지워 이니셜이 보이게 한다.
const artImg = (st) => !(st.art || st.art_url) ? ""
  : `<img class="face" src="${st.art_url || `https://schaledb.com/images/student/icon/${st.art}.webp`}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`;

// AI가 대사 이름을 한국어 대신 id나 영어(Hikari, Tachibana Hikari)로 쓸 때도 학생을 찾는다.
function findStudentByName(name) {
  const n = name.trim();
  const hit = Object.values(state.students).find((s) => s.name === n || s.full_name === n);
  if (hit) return hit;
  const k = n.toLowerCase().replace(/[^a-z_ ]/g, "").trim();
  if (!k) return null;
  return state.students[k] || state.students[k.replace(/\s+/g, "_")] || state.students[k.split(/\s+/).pop()] || null;
}

// 대사 줄의 감정 → 게임식 감정 말풍선 기호. AI는 '이름 [감정]: "대사"' 형식으로 쓴다.
const EMOTES = { 기쁨: "♪", 신남: "✨", 놀람: "!", 의문: "?", 당황: "💦", 부끄러움: "///", 화남: "💢", 슬픔: "💧", 침묵: "…", 졸림: "💤", 결의: "🔥" };
function splitSpeaker(raw) {
  const m = raw.trim().match(/^(.*?)\s*[\[(（【]\s*([가-힣]{1,5})\s*[\])）】]$/);
  return m ? { who: m[1].trim(), emo: m[2] } : { who: raw.trim(), emo: "" };
}

// AI 응답 한 덩어리를 지문 / 대사 / 일반 문단으로 나눠 그린다.
function renderAssistant(text) {
  return text.split(/\n+/).filter((l) => l.trim()).map((raw) => {
    const line = raw.trim();
    const narr = line.match(/^\*(.+)\*$/);
    if (narr) return `<p class="narr">${esc(narr[1])}</p>`;
    const talk = line.match(/^([^:："]{1,28})[:：]\s*["“](.*)["”]$/);
    if (talk) {
      const { who, emo } = splitSpeaker(talk[1]);
      const st = findStudentByName(who);
      const face = st ? halo(st) : `<span class="halo"><span class="face" aria-hidden="true">${esc(who[0] || "?")}</span></span>`;
      const mark = EMOTES[emo] ? `<span class="emote" role="img" aria-label="${esc(emo)}" title="${esc(emo)}">${EMOTES[emo]}</span>` : "";
      const color = st ? `style="--school:${schoolOf(st).color}"` : "";
      return `<div class="line"><span class="face-wrap">${face}${mark}</span><div class="bubble" ${color}><b>${esc(st ? st.name : who)}</b>${esc(talk[2])}</div></div>`;
    }
    return `<p class="plain">${esc(line)}</p>`;
  }).join("");
}

function affectionNote(aff) {
  const parts = Object.entries(aff || {}).filter(([, d]) => d)
    .map(([id, d]) => `${state.students[id]?.name ?? id} ${d > 0 ? "+" : ""}${d}`);
  return parts.length ? `<span class="affection-note">호감도 ${esc(parts.join(", "))}</span>` : "";
}

// ───────── 로그인 ─────────
let signupMode = false;

function showAuth() {
  $("#app").hidden = true;
  $("#auth").hidden = false;
}

$("#auth-toggle").onclick = () => {
  signupMode = !signupMode;
  $("#auth-form").classList.toggle("signup", signupMode);
  $("#auth-submit").textContent = signupMode ? "계정 만들기" : "로그인";
  $("#auth-toggle").textContent = signupMode ? "이미 계정이 있어요" : "처음이신가요? 계정 만들기";
  $("#auth-error").textContent = "";
};

$("#auth-form").onsubmit = async (e) => {
  e.preventDefault();
  const form = Object.fromEntries(new FormData(e.target));
  try {
    const res = await api(signupMode ? "/api/auth/register" : "/api/auth/login", { method: "POST", body: form });
    state.token = res.token;
    localStorage.setItem("token", res.token);
    await enterApp(res.user);
  } catch (err) {
    $("#auth-error").textContent = err.message;
  }
};

function logout() {
  if (state.token) fetch("/api/auth/logout", { method: "POST", headers: { Authorization: `Bearer ${state.token}` } });
  state.token = "";
  localStorage.removeItem("token");
  showAuth();
}
$("#logout").onclick = logout;

async function enterApp(user) {
  state.me = user;
  $("#me-name").textContent = user.sensei_name ? `${user.sensei_name} 선생님` : user.username;
  $("#auth").hidden = true;
  $("#app").hidden = false;
  const [bonds, rooms] = await Promise.all([api("/api/bonds"), api("/api/rooms")]);
  bonds.forEach((b) => (state.bonds[b.student_id] = b));
  state.rooms = rooms;
  renderRooms();
  renderRoster();
  showView("roster");
}

// ───────── 화면 전환 ─────────
function showView(name) {
  for (const v of ["roster", "stories", "world", "chat"]) $(`#view-${v}`).hidden = v !== name;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === name));
  $("#sidebar").classList.remove("open");
  if (name !== "chat") {
    state.room = null;
    renderRooms();
  }
}
document.querySelectorAll(".tab").forEach((t) => (t.onclick = () => showView(t.dataset.view)));
$("#open-sidebar").onclick = () => $("#sidebar").classList.add("open");
$("#close-sidebar").onclick = () => $("#sidebar").classList.remove("open");

// ───────── 학생 명부 ─────────
function renderFilters() {
  const schools = Object.entries(state.catalog.schools);
  $("#school-filter").innerHTML = [["", { name: "전체" }], ...schools]
    .map(([key, s]) => `<button class="chip" data-school="${key}" aria-pressed="${state.schoolFilter === key}">${esc(s.name)}</button>`)
    .join("");
  $("#school-filter").querySelectorAll(".chip").forEach((c) => (c.onclick = () => {
    state.schoolFilter = c.dataset.school;
    renderFilters();
    renderRoster();
  }));
}

function renderRoster() {
  const q = $("#search").value.trim().toLowerCase();
  const list = Object.values(state.students).filter((s) =>
    (!state.schoolFilter || s.school === state.schoolFilter) &&
    (!q || [s.name, s.full_name, s.club, schoolOf(s).name].some((v) => (v || "").toLowerCase().includes(q))));
  $("#roster").innerHTML = list.length
    ? list.map((s) => `<li><button data-id="${s.id}" style="--school:${schoolOf(s).color}">
        ${halo(s)}<span class="who"><strong>${esc(s.name)}${s.detail === "basic" ? '<span class="tag-basic">자료 보강 중</span>' : ""}</strong>
        <span>${esc(schoolOf(s).name)} · ${esc(s.club || "무소속")}</span></span></button></li>`).join("")
    : `<li class="muted">조건에 맞는 학생이 없습니다. 검색어나 학교 필터를 바꿔 보세요.</li>`;
  $("#roster").querySelectorAll("button").forEach((b) => (b.onclick = () => openStudentSheet(b.dataset.id)));
}
$("#search").oninput = renderRoster;

function openStudentSheet(id) {
  const s = state.students[id];
  const bond = state.bonds[id];
  const facts = [["학교", schoolOf(s).name + (s.year ? ` ${s.year}` : "")], ["소속", s.club], ["생일", s.birthday],
    ["키", s.height], ["취미", s.hobby], ["무기", s.weapon]].filter(([, v]) => v);
  const others = state.catalog.world.outfits.filter((o) => !s.outfits?.includes(o));
  $("#sheet-body").innerHTML = `
    <div class="sheet-top">${halo(s, "big")}<div><h2>${esc(s.full_name)}</h2>
      <p class="muted">${bond ? `관계: ${esc(bond.stage)} (${bond.affection}/100)` : "아직 대화한 적이 없습니다."}</p></div></div>
    ${s.personality ? `<p>${esc(s.personality)}</p>` : ""}
    ${s.detail === "basic" ? `<p class="muted">공개된 자료가 적은 학생입니다. 대화 중 설정이 단순할 수 있습니다.</p>` : ""}
    <dl class="facts">${facts.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
    <label>차림
      <select name="outfit"><option value="">평상시 (교복)</option>
        ${s.outfits?.length ? `<optgroup label="게임에 나온 차림">${s.outfits.map((o) => `<option>${esc(o)}</option>`).join("")}</optgroup>` : ""}
        <optgroup label="그 밖의 상황">${others.map((o) => `<option>${esc(o)}</option>`).join("")}</optgroup>
      </select></label>
    <label>상황 설정 (선택)
      <textarea name="situation" rows="3" maxlength="1000" placeholder="예: 비 오는 날 샬레에서 서류 정리를 돕다가 둘만 남았다."></textarea></label>
    <div class="sheet-actions"><button class="btn ghost" value="cancel">닫기</button>
      <button class="btn primary" value="start" id="sheet-start">대화 시작</button></div>`;
  $("#sheet-start").onclick = async (e) => {
    e.preventDefault();
    const f = new FormData($("#sheet-body"));
    $("#sheet").close();
    await createRoom({ mode: "single", student_ids: [id], outfit: f.get("outfit"), situation: f.get("situation") });
  };
  $("#sheet").showModal();
}

// ───────── 스토리 ─────────
function renderScenarios() {
  $("#scenario-list").innerHTML = state.catalog.scenarios.map((sc) => `<li><button data-id="${sc.id}">
      <h2>${esc(sc.title)}</h2><span class="loc">${esc(sc.location)}</span><span>${esc(sc.summary)}</span></button></li>`).join("");
  $("#scenario-list").querySelectorAll("button").forEach((b) => (b.onclick = () => openStorySheet(b.dataset.id)));
}

function openStorySheet(id) {
  const sc = state.catalog.scenarios.find((x) => x.id === id);
  const chosen = new Set(sc.students);
  const all = Object.values(state.students);
  const paint = () => {
    $("#pick").innerHTML = all.filter((s) => chosen.has(s.id) || !$("#pick-q").value || s.name.includes($("#pick-q").value))
      .slice(0, 60)
      .map((s) => `<button type="button" class="chip" data-id="${s.id}" aria-pressed="${chosen.has(s.id)}">${esc(s.name)}</button>`).join("");
    $("#pick").querySelectorAll(".chip").forEach((c) => (c.onclick = () => {
      if (chosen.has(c.dataset.id)) chosen.delete(c.dataset.id);
      else if (chosen.size < 6) chosen.add(c.dataset.id);
      else toast("스토리에는 최대 6명까지 함께할 수 있습니다.");
      paint();
    }));
  };
  $("#sheet-body").innerHTML = `
    <h2>${esc(sc.title)}</h2><p>${esc(sc.summary)}</p>
    <label>함께할 학생 (최대 6명)<input id="pick-q" type="search" placeholder="이름으로 찾아 추가"></label>
    <div id="pick" class="pick"></div>
    <label>상황 설정 ${sc.opening ? "(선택)" : "(자유 시나리오는 적어 주세요)"}
      <textarea name="situation" rows="3" maxlength="1000" placeholder="예: 밀레니엄 학생들과 아비도스로 원정 간다."></textarea></label>
    <div class="sheet-actions"><button class="btn ghost" value="cancel">닫기</button>
      <button class="btn primary" id="sheet-start">이야기 시작</button></div>`;
  $("#pick-q").oninput = paint;
  paint();
  $("#sheet-start").onclick = async (e) => {
    e.preventDefault();
    if (!chosen.size) return toast("학생을 한 명 이상 고르세요.");
    const situation = new FormData($("#sheet-body")).get("situation");
    $("#sheet").close();
    await createRoom({ mode: "story", student_ids: [...chosen], scenario_id: sc.id, situation });
  };
  $("#sheet").showModal();
}

// ───────── 세계관 ─────────
function renderWorld() {
  const w = state.catalog.world.sections.map((s) => `<article><h2>${esc(s.title)}</h2><p>${esc(s.body)}</p></article>`);
  const schools = Object.values(state.catalog.schools).map((s) =>
    `<article><h2 style="color:${s.color}">${esc(s.full_name)}</h2><p>${esc(s.summary)}</p></article>`);
  $("#world").innerHTML = [...w, ...schools].join("");
}

// ───────── 대화방 목록 ─────────
// 서버(SQLite)는 시간대 표시 없이 UTC 시각을 주므로, 표시가 없으면 UTC로 간주한다.
function toDate(s) {
  return new Date(/Z|[+-]\d\d:\d\d$/.test(s) ? s : s + "Z");
}

function renderRooms() {
  $("#room-list").innerHTML = state.rooms.length
    ? state.rooms.map((r) => `<li><button data-id="${r.id}" class="${state.room?.id === r.id ? "active" : ""}">
        <span>${esc(r.title)}</span><span class="room-meta">${r.mode === "story" ? "스토리" : "1:1"} · ${toDate(r.updated_at).toLocaleDateString("ko-KR")}</span>
      </button></li>`).join("")
    : `<li class="muted">아직 대화가 없습니다. 학생 명부에서 학생을 골라 보세요.</li>`;
  $("#room-list").querySelectorAll("button").forEach((b) => (b.onclick = () => openRoom(Number(b.dataset.id))));
}

async function createRoom(body) {
  try {
    const room = await api("/api/rooms", { method: "POST", body });
    state.rooms.unshift(room);
    await openRoom(room.id);
    // 오프닝이 없는 방(1:1, 자유 스토리)은 AI가 먼저 말을 걸게 한다.
    if (!room.messages.length) await runTurn("continue");
  } catch (err) {
    toast(err.message);
  }
}

// ───────── 채팅 ─────────
async function openRoom(id) {
  try {
    state.room = await api(`/api/rooms/${id}`);
  } catch (err) {
    return toast(err.message);
  }
  showView("chat");
  renderChat();
  renderRooms();
}

function roomStudents() {
  return state.room.student_list.map((id) => state.students[id]).filter(Boolean);
}

function renderChatHead() {
  const studs = roomStudents();
  $("#chat-halos").innerHTML = studs.slice(0, 4).map((s) => halo(s, "big")).join("");
  $("#chat-title").textContent = state.room.title;
  $("#chat-sub").textContent = state.room.mode === "story"
    ? studs.map((s) => s.name).join(", ")
    : studs.map((s) => `${state.bonds[s.id]?.stage ?? "익숙함"} · 호감도 ${state.bonds[s.id]?.affection ?? 20}`).join("");
  $("#topbar-title").textContent = state.room.title;
}

function messageHtml(m) {
  return m.role === "user"
    ? `<li class="msg user">${esc(m.content)}</li>`
    : `<li class="msg assistant">${renderAssistant(m.content)}${affectionNote(m.affection)}</li>`;
}

function renderChat() {
  renderChatHead();
  const msgs = state.room.messages;
  $("#messages").innerHTML = msgs.length ? msgs.map(messageHtml).join("") : `<li class="muted">첫 마디를 건네 보세요.</li>`;
  scrollDown();
}

function scrollDown() {
  const box = $("#messages");
  box.scrollTop = box.scrollHeight;
}

function setBusy(on) {
  state.busy = on;
  ["#send", "#btn-continue", "#btn-regen", "#btn-undo"].forEach((s) => ($(s).disabled = on));
  $("#messages").querySelector(".typing")?.remove();
  if (on) {
    $("#messages").insertAdjacentHTML("beforeend", `<li class="typing">답장을 쓰는 중…</li>`);
    scrollDown();
  }
}

// kind: "send" | "continue" | "regenerate"
async function runTurn(kind, content = "") {
  if (state.busy || !state.room) return;
  const room = state.room;
  const path = { send: "messages", continue: "continue", regenerate: "regenerate" }[kind];
  setBusy(true);
  try {
    const res = await api(`/api/rooms/${room.id}/${path}`, { method: "POST", body: { content, provider: $("#provider").value } });
    if (kind === "regenerate") room.messages.pop();
    room.messages.push(...res.messages);
    res.bonds.forEach((b) => (state.bonds[b.student_id] = b));
    if (res.summarized) toast("대화가 길어져 앞부분을 기억으로 정리했습니다.");
    if (state.room === room) {
      renderChat();
      const changed = res.messages.at(-1).affection || {};
      Object.keys(changed).forEach((id) => document.querySelectorAll(`[data-halo="${id}"]`).forEach((h) => h.classList.add("bump")));
    }
    bumpRoom(room.id);
  } catch (err) {
    toast(err.message);
    return false;
  } finally {
    setBusy(false);
  }
  return true;
}

function bumpRoom(id) {
  const i = state.rooms.findIndex((r) => r.id === id);
  if (i > 0) state.rooms.unshift(...state.rooms.splice(i, 1));
  if (i >= 0) state.rooms[0].updated_at = new Date().toISOString();
  renderRooms();
}

$("#composer").onsubmit = async (e) => {
  e.preventDefault();
  const text = $("#input").value.trim();
  if (!text || state.busy) return;
  $("#input").value = "";
  // 서버 응답을 기다리는 동안 내 메시지를 먼저 보여 준다 (응답이 오면 진짜 메시지로 다시 그린다)
  $("#messages").insertAdjacentHTML("beforeend", messageHtml({ role: "user", content: text }));
  if (!(await runTurn("send", text))) {
    renderChat();
    $("#input").value = text; // 실패하면 입력을 돌려준다
  }
};
$("#input").onkeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    $("#composer").requestSubmit();
  }
};
$("#btn-continue").onclick = () => runTurn("continue");
$("#btn-regen").onclick = () => runTurn("regenerate");
$("#btn-undo").onclick = async () => {
  if (state.busy) return;
  try {
    const room = await api(`/api/rooms/${state.room.id}/messages/last`, { method: "DELETE" });
    state.room = room;
    const bonds = await api("/api/bonds");
    bonds.forEach((b) => (state.bonds[b.student_id] = b));
    renderChat();
  } catch (err) {
    toast(err.message);
  }
};
$("#delete-room").onclick = async () => {
  if (!confirm("이 대화를 삭제할까요? 되돌릴 수 없습니다. (호감도는 유지됩니다)")) return;
  await api(`/api/rooms/${state.room.id}`, { method: "DELETE" });
  state.rooms = state.rooms.filter((r) => r.id !== state.room.id);
  showView("roster");
};

// ───────── 시작 ─────────
async function boot() {
  state.catalog = await api("/api/catalog");
  state.catalog.students.forEach((s) => (state.students[s.id] = s));
  $("#provider").innerHTML = state.catalog.providers
    .map((p) => `<option value="${p.key}" ${p.key === state.catalog.default_provider ? "selected" : ""}>${esc(p.label)}</option>`).join("");
  renderFilters();
  renderScenarios();
  renderWorld();
  if (!state.token) return showAuth();
  try {
    await enterApp(await api("/api/me"));
  } catch {
    showAuth();
  }
}
boot();
