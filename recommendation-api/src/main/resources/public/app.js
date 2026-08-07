const state = {
  demoUsers: [],
  feeds: new Map(),
  datasetTotal: 0,
};

const el = (id) => document.getElementById(id);

function showToast(message) {
  const toast = el("toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 3200);
}

async function fetchJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const message = payload.error || `${response.status} ${response.statusText}`;
    throw new Error(message);
  }
  return payload;
}

function fmtDate(value) {
  if (!value) return "unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function score(value) {
  if (typeof value !== "number") return "-";
  return value.toFixed(3);
}

function setBusy(button, busy) {
  if (!button) return;
  button.disabled = busy;
}

function renderDataset(dataset) {
  state.datasetTotal = dataset.totalIndexed;
  el("indexed-count").textContent = dataset.totalIndexed.toLocaleString();
  el("visible-count").textContent = dataset.visible.toLocaleString();
  el("updated-at").textContent = fmtDate(dataset.generatedAt);

  const list = el("dataset-list");
  const empty = el("dataset-empty");
  list.innerHTML = "";

  if (!dataset.items.length) {
    empty.classList.remove("hidden");
    return;
  }

  empty.classList.add("hidden");
  for (const post of dataset.items) {
    const card = document.createElement("article");
    card.className = "post-card";
    card.innerHTML = `
      <div class="meta">
        <span class="chip blue">${escapeHtml(post.language)}</span>
        <span class="chip">${escapeHtml(post.authorId)}</span>
        <span class="chip amber">${fmtDate(post.createdAt)}</span>
      </div>
      <p>${escapeHtml(post.text)}</p>
      <div class="meta">
        <span class="chip rose">${escapeHtml(post.postId)}</span>
        <span class="chip">${escapeHtml(post.source || "unknown")}</span>
      </div>
    `;
    list.appendChild(card);
  }
}

function renderPeople() {
  const grid = el("people-grid");
  grid.innerHTML = "";

  for (const user of state.demoUsers) {
    const card = document.createElement("article");
    card.className = "person-card";
    card.dataset.userId = user.userId;
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `${user.displayName} feed`);
    card.innerHTML = `
      <div class="person-head">
        <div>
          <p class="eyebrow">${escapeHtml(user.userId)}</p>
          <h3>${escapeHtml(user.displayName)}</h3>
        </div>
        <div class="person-actions">
          <button class="secondary" data-action="build">Save</button>
          <button class="primary" data-action="feed">Feed</button>
        </div>
      </div>
      <div class="interests">
        ${user.interests.map((interest) => `<span class="chip">${escapeHtml(interest)}</span>`).join("")}
      </div>
      <div class="feed-list" data-feed></div>
    `;
    grid.appendChild(card);
  }

  grid.querySelectorAll(".person-card").forEach((card) => {
    card.addEventListener("click", async (event) => {
      if (event.target.closest("button")) return;
      const userId = card.dataset.userId;
      const user = state.demoUsers.find((item) => item.userId === userId);
      if (user) await openPerson(user, card);
    });
    card.addEventListener("keydown", async (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      const userId = card.dataset.userId;
      const user = state.demoUsers.find((item) => item.userId === userId);
      if (user) await openPerson(user, card);
    });
  });

  grid.querySelectorAll("button[data-action='build']").forEach((button) => {
    button.addEventListener("click", async (event) => {
      const userId = event.target.closest(".person-card").dataset.userId;
      const user = state.demoUsers.find((item) => item.userId === userId);
      if (user) await openPerson(user, event.target);
    });
  });

  grid.querySelectorAll("button[data-action='feed']").forEach((button) => {
    button.addEventListener("click", async (event) => {
      const userId = event.target.closest(".person-card").dataset.userId;
      const user = state.demoUsers.find((item) => item.userId === userId);
      if (user) await openPerson(user, event.target);
    });
  });
}

async function openPerson(user, trigger) {
  const card = document.querySelector(`.person-card[data-user-id="${CSS.escape(user.userId)}"]`);
  selectPerson(user.userId);
  setCardBusy(card, true);
  const target = card ? card.querySelector("[data-feed]") : null;
  if (target) {
    target.innerHTML = `<div class="empty">Loading ${escapeHtml(user.displayName)} feed from indexed posts...</div>`;
  }
  try {
    await loadDataset();
    await buildProfile(user, trigger);
    await loadFeed(user.userId);
  } catch (error) {
    if (target) {
      target.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    }
    showToast(error.message);
  } finally {
    setCardBusy(card, false);
  }
}

function selectPerson(userId) {
  document.querySelectorAll(".person-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.userId === userId);
  });
}

function setCardBusy(card, busy) {
  if (!card) return;
  card.classList.toggle("loading", busy);
  card.querySelectorAll("button").forEach((button) => {
    button.disabled = busy;
  });
}

function renderFeed(userId, feed) {
  const card = document.querySelector(`.person-card[data-user-id="${CSS.escape(userId)}"]`);
  const target = card ? card.querySelector("[data-feed]") : el("custom-feed");
  target.innerHTML = "";

  if (!feed.items.length) {
    target.innerHTML = `<div class="empty">No matching indexed posts yet.</div>`;
    return;
  }

  const context = document.createElement("div");
  context.className = "feed-context";
  context.textContent = `${feed.items.length} recommendations pulled from ${state.datasetTotal.toLocaleString()} indexed posts`;
  target.appendChild(context);
  for (const item of feed.items.slice(0, 6)) {
    target.appendChild(feedItemElement(item));
  }
}

function renderCustomFeed(feed) {
  const target = el("custom-feed");
  target.innerHTML = "";
  if (!feed.items.length) {
    target.innerHTML = `<div class="empty">No matching indexed posts yet.</div>`;
    return;
  }
  const context = document.createElement("div");
  context.className = "feed-context";
  context.textContent = `${feed.items.length} recommendations pulled from ${state.datasetTotal.toLocaleString()} indexed posts`;
  target.appendChild(context);
  for (const item of feed.items.slice(0, 8)) {
    target.appendChild(feedItemElement(item));
  }
}

function feedItemElement(item) {
  const node = document.createElement("article");
  node.className = "feed-item";
  node.innerHTML = `
    <div class="meta">
      <span class="chip">${escapeHtml(item.authorId)}</span>
      <span class="chip blue">${fmtDate(item.createdAt)}</span>
      <span class="chip rose">${escapeHtml(item.postId)}</span>
    </div>
    <p>${escapeHtml(item.text)}</p>
    <div class="feed-score">
      <span>semantic<strong>${score(item.semanticScore)}</strong></span>
      <span>recency<strong>${score(item.recencyScore)}</strong></span>
      <span>final<strong>${score(item.finalScore)}</strong></span>
    </div>
  `;
  return node;
}

async function loadHealth() {
  try {
    await fetchJson("/health");
    el("api-status").textContent = "ok";
  } catch (error) {
    el("api-status").textContent = "down";
    showToast(error.message);
  }
}

async function loadDataset() {
  const limit = Number.parseInt(el("dataset-limit").value || "80", 10);
  const dataset = await fetchJson(`/posts?limit=${encodeURIComponent(limit)}`);
  renderDataset(dataset);
}

async function loadDemoUsers() {
  const payload = await fetchJson("/demo/users");
  state.demoUsers = payload.users;
  renderPeople();
}

async function seedAllProfiles() {
  const button = el("seed-all");
  setBusy(button, true);
  try {
    const response = await fetchJson("/demo/users", { method: "POST", body: "{}" });
    showToast(`Seeded ${response.profiles.length} profiles`);
    await loadAllFeeds();
  } finally {
    setBusy(button, false);
  }
}

async function ensureDemoProfiles() {
  const response = await fetchJson("/demo/users", { method: "POST", body: "{}" });
  showToast(`Profiles ready for ${response.profiles.length} people`);
}

async function buildProfile(user, button) {
  setBusy(button, true);
  try {
    await fetchJson(`/users/${encodeURIComponent(user.userId)}/interests`, {
      method: "POST",
      body: JSON.stringify({ interests: user.interests }),
    });
    showToast(`Profile saved for ${user.displayName}`);
  } finally {
    setBusy(button, false);
  }
}

async function loadFeed(userId) {
  try {
    const feed = await fetchJson(`/users/${encodeURIComponent(userId)}/feed?limit=12`);
    state.feeds.set(userId, feed);
    renderFeed(userId, feed);
  } catch (error) {
    const card = document.querySelector(`.person-card[data-user-id="${CSS.escape(userId)}"]`);
    const target = card ? card.querySelector("[data-feed]") : el("custom-feed");
    target.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  }
}

async function loadAllFeeds() {
  const button = el("load-feeds");
  setBusy(button, true);
  try {
    await ensureDemoProfiles();
    await Promise.all(state.demoUsers.map((user) => loadFeed(user.userId)));
  } finally {
    setBusy(button, false);
  }
}

async function saveCustomProfile() {
  const button = el("save-custom");
  const userId = el("custom-user-id").value.trim();
  const interests = el("custom-interests")
    .value.split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

  if (!userId || interests.length === 0) {
    showToast("User ID and interests are required");
    return;
  }

  setBusy(button, true);
  try {
    await fetchJson(`/users/${encodeURIComponent(userId)}/interests`, {
      method: "POST",
      body: JSON.stringify({ interests }),
    });
    const feed = await fetchJson(`/users/${encodeURIComponent(userId)}/feed?limit=12`);
    await loadDataset();
    renderCustomFeed(feed);
    showToast(`Profile saved for ${userId}`);
  } finally {
    setBusy(button, false);
  }
}

async function refreshAll() {
  const button = el("refresh-all");
  setBusy(button, true);
  try {
    await loadHealth();
    await loadDataset();
    if (!state.demoUsers.length) {
      await loadDemoUsers();
    }
    await loadAllFeeds();
  } finally {
    setBusy(button, false);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

window.addEventListener("DOMContentLoaded", async () => {
  el("refresh-all").addEventListener("click", refreshAll);
  el("seed-all").addEventListener("click", seedAllProfiles);
  el("refresh-dataset").addEventListener("click", async () => {
    try {
      await loadDataset();
    } catch (error) {
      showToast(error.message);
    }
  });
  el("load-feeds").addEventListener("click", loadAllFeeds);
  el("save-custom").addEventListener("click", saveCustomProfile);

  try {
    await loadHealth();
    await loadDemoUsers();
    await loadDataset();
  } catch (error) {
    showToast(error.message);
  }
});
