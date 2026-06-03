// Entry point for the browser demo. Wires the WebSocket event stream to the
// avatar renderer and the onboarding / subtitle / composer UI. Deliberately small
// — all the thinking happens in the Python core.

import { KomorebiSocket } from "./ws.js";
import { ServerMsg, userMessage, hello } from "./protocol.js";
import { PlaceholderAvatar } from "./avatar/PlaceholderAvatar.js";

const els = {
  canvas: document.getElementById("stage"),
  subtitle: document.getElementById("subtitle"),
  status: document.getElementById("status"),
  input: document.getElementById("input"),
  form: document.getElementById("composer"),
  samples: document.getElementById("samples"),
  onboard: document.getElementById("onboard"),
  personaList: document.getElementById("personaList"),
  start: document.getElementById("start"),
};

const SAMPLE_PROMPTS = ["こんにちは！", "今日あったこと聞いてくれる？", "おすすめの過ごし方は？", "ちょっと元気ないんだ…"];

// Renderer selection. Default is the dependency-free placeholder; ?renderer=vrm
// opts into the 3D VRM renderer (loaded lazily). VRM needs a model — provide one
// via ?vrm=<url> or drop a file at web/assets/avatar.vrm. On any failure we fall
// back to the placeholder so the demo always works.
let avatar = null;

async function setupAvatar() {
  const params = new URLSearchParams(location.search);
  const wanted = params.get("renderer") || "placeholder";

  if (wanted === "vrm") {
    const url = params.get("vrm") || "/assets/avatar.vrm";
    try {
      const { VrmAvatar } = await import("./avatar/VrmAvatar.js");
      const vrm = new VrmAvatar();
      vrm.mount(els.canvas);
      await vrm.loadModel(url);
      avatar = vrm;
      return;
    } catch (err) {
      console.warn("VRM renderer unavailable, falling back to placeholder:", err);
      els.status.textContent = "VRMモデルを読み込めませんでした。プレースホルダーに切替。";
    }
  }

  const placeholder = new PlaceholderAvatar();
  placeholder.mount(els.canvas);
  avatar = placeholder;
}

let speechStartedAt = 0;
let sock = null;
let selectedPersona = null;
let pendingTimers = [];

function clearTimers() {
  pendingTimers.forEach(clearTimeout);
  pendingTimers = [];
}

// ---- onboarding: load personas, let the user pick one --------------------

async function loadPersonas() {
  try {
    const res = await fetch("/personas");
    const data = await res.json();
    selectedPersona = data.default;
    renderPersonas(data.personas, data.default);
  } catch {
    els.personaList.textContent = "（コアに接続できませんでした。サーバーは起動していますか？）";
  }
}

function renderPersonas(personas, defaultId) {
  els.personaList.innerHTML = "";
  for (const p of personas) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "persona";
    btn.setAttribute("aria-pressed", String(p.id === defaultId));
    btn.innerHTML = `<div class="pname">${p.name}</div><div class="ptag">${p.tagline ?? ""}</div>`;
    btn.addEventListener("click", () => {
      selectedPersona = p.id;
      [...els.personaList.children].forEach((c) => c.setAttribute("aria-pressed", "false"));
      btn.setAttribute("aria-pressed", "true");
    });
    els.personaList.appendChild(btn);
  }
}

function renderSamples() {
  els.samples.innerHTML = "";
  for (const text of SAMPLE_PROMPTS) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = text;
    chip.addEventListener("click", () => sendMessage(text));
    els.samples.appendChild(chip);
  }
}

// ---- conversation ---------------------------------------------------------

function connect(personaId) {
  clearTimers();
  if (sock) sock.close();
  const wsUrl = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws";
  sock = new KomorebiSocket(wsUrl);
  sock
    .on(ServerMsg.READY, (m) => {
      els.status.textContent = `connected · ${m.persona?.name ?? "?"}`;
    })
    .on(ServerMsg.SPEECH_START, () => {
      speechStartedAt = performance.now();
      avatar?.speechStart();
    })
    .on(ServerMsg.EXPRESSION, (m) => scheduleAt(m.t, () => avatar?.setExpression(m)))
    .on(ServerMsg.VISEME, (m) => scheduleAt(m.t, () => avatar?.setViseme({ phoneme: m.phoneme })))
    .on(ServerMsg.SUBTITLE, (m) => {
      els.subtitle.textContent = m.text;
    })
    .on(ServerMsg.SPEECH_END, () => avatar?.speechEnd())
    .on(ServerMsg.ERROR, (m) => {
      els.status.textContent = `error: ${m.message}`;
    });

  return sock
    .connect()
    .then(() => {
      sock.send(hello(personaId));
      els.status.textContent = "connected";
    })
    .catch(() => {
      els.status.textContent = "could not connect to Komorebi core (is it running?)";
    });
}

// Schedule a callback `t` seconds after the current speech started.
function scheduleAt(t, fn) {
  const delay = Math.max(0, (t ?? 0) * 1000 - (performance.now() - speechStartedAt));
  pendingTimers.push(setTimeout(fn, delay));
}

function sendMessage(text) {
  const value = (text ?? "").trim();
  if (!value || !sock) return;
  els.subtitle.textContent = value;
  sock.send(userMessage(value));
  els.input.value = "";
}

// ---- wiring ---------------------------------------------------------------

els.form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  sendMessage(els.input.value);
});

els.start.addEventListener("click", async () => {
  els.onboard.classList.add("hidden");
  await connect(selectedPersona);
});

setupAvatar();
renderSamples();
loadPersonas();
