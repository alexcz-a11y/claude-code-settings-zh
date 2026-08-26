const $ = (sel) => document.querySelector(sel);

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function codeish(s) {
  return esc(s).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function card(item) {
  const values = item.typeValues?.length
    ? `<div class="values">${item.typeValues.map((v) => `<div class="val">${codeish(v)}</div>`).join("")}</div>`
    : `<p>${codeish(item.type === "未在官方文档写明" ? "未在官方文档写明" : "见上方类型说明")}</p>`;
  const numeric = item.numeric
    ? `<div class="row"><dt>数字含义</dt><dd>${codeish(item.numeric)}</dd></div>`
    : "";
  const overrides = item.overrides
    ? `<div class="row"><dt>会话覆盖</dt><dd>${codeish(item.overrides)}</dd></div>`
    : "";
  const schema = item.inSchema
    ? ""
    : `<span class="chip">Schema 尚未收录顶层键</span>`;
  return `<article class="card" data-key="${esc(item.key)}" id="${esc(item.anchor)}">
    <div class="card-kicker">
      <span class="chip accent">${esc(item.scopeZh)}</span>
      <span class="chip">${esc(item.topicZh)}</span>
      ${schema}
    </div>
    <p class="key mono">${esc(item.key)}</p>
    <h3 class="zh-name">${esc(item.zhName)}</h3>
    <p class="meaning">${esc(item.zhMeaning)}</p>
    <div class="rows">
      <div class="row"><dt>类型</dt><dd>${codeish(item.type)}</dd></div>
      <div class="row"><dt>允许值 / 枚举</dt><dd>${values}</dd></div>
      <div class="row"><dt>默认值</dt><dd>${codeish(item.default)}</dd></div>
      <div class="row"><dt>作用范围</dt><dd>${esc(item.scopeZh)}${item.scopeDetail ? ` · ${codeish(item.scopeDetail)}` : ""}</dd></div>
      ${numeric}
      ${overrides}
    </div>
    <a class="src" href="${esc(item.source)}" rel="noopener">官方条目</a>
  </article>`;
}

function renderList(items, mount, emptyText) {
  if (!items.length) {
    mount.innerHTML = `<p class="empty">${esc(emptyText)}</p>`;
    return;
  }
  const topics = [];
  for (const item of items) {
    const last = topics[topics.length - 1];
    if (!last || last.id !== item.topic) topics.push({ id: item.topic, zh: item.topicZh, items: [item] });
    else last.items.push(item);
  }
  mount.innerHTML = topics
    .map((g) => `<section class="group"><h2>${esc(g.zh)}</h2>${g.items.map(card).join("")}</section>`)
    .join("");
}

function match(item, q) {
  if (!q) return true;
  const hay = [
    item.key,
    item.zhName,
    item.zhMeaning,
    item.descEn,
    item.topic,
    item.topicZh,
    item.scope,
    item.scopeZh,
    item.type,
    item.default,
    ...(item.typeValues || []),
  ]
    .join("\n")
    .toLowerCase();
  return q.split(/\s+/).every((part) => hay.includes(part));
}

const data = await fetch("./data/keys.json").then((r) => r.json());
const settingsKeys = data.keys.filter((k) => k.kind === "settings");
const globalKeys = data.keys.filter((k) => k.kind === "global");

function paint() {
  const q = ($("#q").value || "").trim().toLowerCase();
  const tab = document.querySelector(".seg-btn.is-on")?.dataset.tab || "settings";
  const settingsHit = settingsKeys.filter((k) => match(k, q));
  const globalHit = globalKeys.filter((k) => match(k, q));
  $("#count").textContent = q
    ? `官方 All settings ${data.officialIndexCount} 项里，settings.json 侧匹配 ${settingsHit.length} 项`
    : `官方 All settings ${data.officialIndexCount} 项 · settings.json 侧 ${settingsKeys.length} 项`;
  $("#count-global").textContent = q
    ? `全局配置匹配 ${globalHit.length} / ${globalKeys.length}`
    : `官方 Global config ${globalKeys.length} 项`;
  renderList(settingsHit, $("#results"), "没有匹配的 settings.json 字段");
  renderList(globalHit, $("#results-global"), "没有匹配的 ~/.claude.json 字段");

  const schemaMount = $("#results-global");
  if (tab === "global" && !q && data.schemaOnlyKeys?.length) {
    schemaMount.insertAdjacentHTML(
      "beforeend",
      `<section class="group"><h2>仅出现在 Schema</h2>
      ${data.schemaOnlyKeys
        .map(
          (k) => `<article class="card">
            <p class="key mono">${esc(k.key)}</p>
            <p class="meaning">未在官方文档写明。${esc(k.note)}</p>
            <a class="src" href="${esc(k.source)}" rel="noopener">Schema</a>
          </article>`
        )
        .join("")}</section>`
    );
  }
}

function setTab(tab) {
  document.querySelectorAll(".seg-btn").forEach((btn) => {
    const on = btn.dataset.tab === tab;
    btn.classList.toggle("is-on", on);
    btn.setAttribute("aria-selected", on ? "true" : "false");
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    const on = panel.dataset.panel === tab;
    panel.classList.toggle("is-on", on);
    panel.hidden = !on;
  });
  paint();
}

document.querySelectorAll(".seg-btn").forEach((btn) => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});
$("#q").addEventListener("input", paint);
paint();
