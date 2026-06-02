// PlaceholderAvatar — a dependency-free 2D face drawn on a canvas.
//
// It proves the avatar-agnostic pipeline end to end without any model assets: it
// reacts to abstract emotions (eyes/brows/color) and lip-syncs from viseme frames
// (mouth openness per vowel). VRM and Live2D renderers (M2) implement the same
// AvatarBackend interface and slot in unchanged.

import { AvatarBackend } from "./AvatarBackend.js";

const EMOTION_STYLE = {
  neutral:  { face: "#f4d9c0", brow: 0.0,  mouthCurve: 0.0,  eye: 1.0 },
  joy:      { face: "#ffe2c0", brow: 0.2,  mouthCurve: 0.6,  eye: 0.8 },
  sadness:  { face: "#e6dcd0", brow: -0.3, mouthCurve: -0.5, eye: 0.7 },
  anger:    { face: "#f6c9b0", brow: -0.5, mouthCurve: -0.3, eye: 1.1 },
  surprise: { face: "#ffe6cc", brow: 0.5,  mouthCurve: 0.0,  eye: 1.4 },
  fear:     { face: "#e9dad0", brow: 0.3,  mouthCurve: -0.2, eye: 1.3 },
  thinking: { face: "#efe0cd", brow: 0.1,  mouthCurve: 0.0,  eye: 0.9 },
};

const VISEME_OPEN = { rest: 0.05, a: 1.0, i: 0.3, u: 0.4, e: 0.6, o: 0.8 };

export class PlaceholderAvatar extends AvatarBackend {
  constructor() {
    super();
    this.canvas = null;
    this.ctx = null;
    this.style = EMOTION_STYLE.neutral;
    this.intensity = 0.2;
    this.mouthOpen = 0.05;
    this.blink = 1.0;
    this._raf = null;
  }

  mount(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this._loop();
    // Idle blinking.
    setInterval(() => {
      this.blink = 0.1;
      setTimeout(() => (this.blink = 1.0), 120);
    }, 3500);
  }

  setExpression({ emotion, intensity }) {
    this.style = EMOTION_STYLE[emotion] ?? EMOTION_STYLE.neutral;
    this.intensity = intensity ?? 0.5;
  }

  setViseme({ phoneme }) {
    const target = VISEME_OPEN[phoneme] ?? 0.05;
    this.mouthOpen = target;
    // Relax mouth shortly after, so frames read as articulation.
    clearTimeout(this._mouthTimer);
    this._mouthTimer = setTimeout(() => (this.mouthOpen = 0.05), 90);
  }

  speechEnd() {
    this.mouthOpen = 0.05;
  }

  _loop() {
    const draw = () => {
      this._draw();
      this._raf = requestAnimationFrame(draw);
    };
    draw();
  }

  _draw() {
    const { ctx } = this;
    if (!ctx) return;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const k = this.intensity; // emotion strength

    ctx.clearRect(0, 0, w, h);

    // Face
    ctx.fillStyle = this.style.face;
    ctx.beginPath();
    ctx.ellipse(cx, cy, 110, 130, 0, 0, Math.PI * 2);
    ctx.fill();

    // Eyes
    const eyeY = cy - 20;
    const eyeDx = 45;
    const eyeR = 14 * this.style.eye;
    for (const sign of [-1, 1]) {
      ctx.fillStyle = "#3a2c22";
      ctx.beginPath();
      ctx.ellipse(cx + sign * eyeDx, eyeY, eyeR, eyeR * this.blink, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    // Brows (tilt encodes emotion)
    const browTilt = this.style.brow * k * 18;
    ctx.strokeStyle = "#5a4636";
    ctx.lineWidth = 5;
    for (const sign of [-1, 1]) {
      const bx = cx + sign * eyeDx;
      ctx.beginPath();
      ctx.moveTo(bx - 18, eyeY - 28 + sign * browTilt);
      ctx.lineTo(bx + 18, eyeY - 28 - sign * browTilt);
      ctx.stroke();
    }

    // Mouth: width fixed, height = openness, corners curve = valence
    const mouthY = cy + 55;
    const open = 6 + this.mouthOpen * 40;
    const curve = this.style.mouthCurve * k * 22;
    ctx.fillStyle = "#7a3b34";
    ctx.beginPath();
    ctx.moveTo(cx - 35, mouthY);
    ctx.quadraticCurveTo(cx, mouthY - curve, cx + 35, mouthY);
    ctx.quadraticCurveTo(cx, mouthY + open + curve, cx - 35, mouthY);
    ctx.fill();
  }
}
