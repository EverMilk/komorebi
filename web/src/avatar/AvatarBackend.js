// AvatarBackend — the renderer-agnostic interface.
//
// Every avatar (placeholder 2D, VRM, Live2D) implements these methods. They
// receive only normalized events from the core; they never learn which LLM or TTS
// produced them. That indirection is the whole "swap any avatar" promise.
//
// This is documented as an interface via JSDoc rather than enforced (build-less
// M0). In M2 it becomes a TypeScript interface.
//
// @typedef {Object} ExpressionEvent
// @property {string} emotion   one of EMOTIONS
// @property {number} intensity 0..1
//
// @typedef {Object} VisemeEvent
// @property {string} phoneme  "a"|"i"|"u"|"e"|"o"|"rest"
// @property {number} t        seconds offset from speech start

/**
 * @interface
 */
export class AvatarBackend {
  /** Called once with the canvas to draw into. */
  // eslint-disable-next-line no-unused-vars
  mount(canvas) { throw new Error("not implemented"); }

  /** Apply an abstract expression. @param {ExpressionEvent} e */
  // eslint-disable-next-line no-unused-vars
  setExpression(e) { throw new Error("not implemented"); }

  /** Drive the mouth for one viseme frame. @param {VisemeEvent} v */
  // eslint-disable-next-line no-unused-vars
  setViseme(v) { throw new Error("not implemented"); }

  /** Speech started — begin any idle->talking transition. */
  speechStart() {}

  /** Speech finished — return mouth to rest. */
  speechEnd() {}
}
