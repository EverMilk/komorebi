// Entry point for the browser demo. Wires the WebSocket event stream to the
// avatar renderer and the subtitle/composer UI. Deliberately small — all the
// thinking happens in the Python core.

import { KomorebiSocket } from "./ws.js";
import { ServerMsg, userMessage, hello } from "./protocol.js";
import { PlaceholderAvatar } from "./avatar/PlaceholderAvatar.js";

const canvas = document.getElementById("stage");
const subtitleEl = document.getElementById("subtitle");
const statusEl = document.getElementById("status");
const inputEl = document.getElementById("input");
const formEl = document.getElementById("composer");

const avatar = new PlaceholderAvatar();
avatar.mount(canvas);

// Schedule viseme frames relative to the moment speech started.
let speechStartedAt = 0;

const wsUrl = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws";
const sock = new KomorebiSocket(wsUrl);

sock
  .on(ServerMsg.READY, (m) => {
    statusEl.textContent = `connected · ${m.persona?.name ?? "?"}`;
  })
  .on(ServerMsg.SPEECH_START, () => {
    speechStartedAt = performance.now();
    avatar.speechStart();
  })
  .on(ServerMsg.EXPRESSION, (m) => {
    avatar.setExpression({ emotion: m.emotion, intensity: m.intensity });
  })
  .on(ServerMsg.VISEME, (m) => {
    // m.t is seconds from speech start; schedule the mouth frame.
    const delay = Math.max(0, m.t * 1000 - (performance.now() - speechStartedAt));
    setTimeout(() => avatar.setViseme({ phoneme: m.phoneme }), delay);
  })
  .on(ServerMsg.SUBTITLE, (m) => {
    subtitleEl.textContent = m.text;
  })
  .on(ServerMsg.SPEECH_END, () => {
    avatar.speechEnd();
  })
  .on(ServerMsg.ERROR, (m) => {
    statusEl.textContent = `error: ${m.message}`;
  });

formEl.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  subtitleEl.textContent = text;
  sock.send(userMessage(text));
  inputEl.value = "";
});

(async () => {
  try {
    await sock.connect();
    sock.send(hello(null)); // use server default persona
    statusEl.textContent = "connected";
  } catch {
    statusEl.textContent = "could not connect to Komorebi core (is it running?)";
  }
})();
