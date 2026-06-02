// WebSocket wire contract (browser side).
//
// This mirrors core/komorebi/protocol.py. The schema is the frozen boundary
// between the Python core and this renderer — see docs/architecture.md. Keep the
// two files in sync. (Migrates to protocol.ts in M2.)

export const ClientMsg = Object.freeze({
  HELLO: "hello",
  USER_MESSAGE: "user_message",
});

export const ServerMsg = Object.freeze({
  READY: "ready",
  SPEECH_START: "speech_start",
  SUBTITLE: "subtitle",
  EXPRESSION: "expression",
  VISEME: "viseme",
  AUDIO: "audio",
  SPEECH_END: "speech_end",
  ERROR: "error",
});

// Abstract emotion vocabulary. Renderers map these to their own parameters.
export const EMOTIONS = Object.freeze([
  "neutral", "joy", "sadness", "anger", "surprise", "fear", "thinking",
]);

export function hello(persona) {
  return { type: ClientMsg.HELLO, persona: persona ?? null };
}

export function userMessage(text) {
  return { type: ClientMsg.USER_MESSAGE, text };
}
