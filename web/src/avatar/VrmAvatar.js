// VrmAvatar — a real 3D renderer built on three.js + @pixiv/three-vrm.
//
// It implements the exact same AvatarBackend interface as PlaceholderAvatar, so
// the core drives it with the identical normalized events (abstract emotion +
// viseme). Swapping `placeholder` for `vrm` changes nothing upstream — that is the
// whole point of the avatar abstraction.
//
// three / three-vrm are resolved from the importmap in index.html and only loaded
// when this module is dynamically imported (i.e. when ?renderer=vrm is selected),
// so placeholder users pay zero download cost.
//
// VRM models are NOT bundled (they carry their own licenses). Provide one via
// ?vrm=<url> or by dropping a file at web/assets/avatar.vrm. See
// docs/avatar-renderers.md.

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

import { AvatarBackend } from "./AvatarBackend.js";

// Abstract emotion -> VRM expression preset.
const EMOTION_PRESET = {
  neutral: "neutral",
  joy: "happy",
  sadness: "sad",
  anger: "angry",
  surprise: "surprised",
  fear: "sad",
  thinking: "relaxed",
};

// Viseme phoneme -> VRM mouth preset.
const VISEME_PRESET = { a: "aa", i: "ih", u: "ou", e: "ee", o: "oh" };

const EMOTION_PRESETS = ["neutral", "happy", "sad", "angry", "surprised", "relaxed"];
const MOUTH_PRESETS = ["aa", "ih", "ou", "ee", "oh"];

const lerp = (a, b, t) => a + (b - a) * t;

export class VrmAvatar extends AvatarBackend {
  constructor() {
    super();
    this.vrm = null;
    this.clock = new THREE.Clock();
    // target / current weights for smooth transitions
    this.emotion = {}; // preset -> target weight
    this.emoNow = {}; // preset -> current weight
    this.mouth = {}; // preset -> target weight
    this.mouthNow = {};
    this.blink = 0;
    this._nextBlink = 0;
  }

  mount(canvas) {
    const w = canvas.width || canvas.clientWidth || 320;
    const h = canvas.height || canvas.clientHeight || 320;

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setSize(w, h, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(28, w / h, 0.1, 20);
    this.camera.position.set(0, 1.32, 1.1);
    this.cameraTarget = new THREE.Vector3(0, 1.3, 0);

    const key = new THREE.DirectionalLight(0xffffff, 2.0);
    key.position.set(1, 1.5, 1.2);
    this.scene.add(key);
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.9));

    this._animate();
  }

  // Async because the model is fetched. Throws on failure so the caller can fall
  // back to the placeholder renderer.
  async loadModel(url) {
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));
    const gltf = await loader.loadAsync(url);
    const vrm = gltf.userData.vrm;

    VRMUtils.removeUnnecessaryVertices(gltf.scene);
    VRMUtils.combineSkeletons(gltf.scene);
    VRMUtils.rotateVRM0(vrm); // make VRM0 models face the camera (+Z); no-op for VRM1

    vrm.scene.traverse((o) => (o.frustumCulled = false));
    this.scene.add(vrm.scene);

    // Eye contact: look at the camera.
    if (vrm.lookAt) {
      const target = new THREE.Object3D();
      this.camera.add(target);
      this.scene.add(this.camera);
      vrm.lookAt.target = target;
    }

    // Frame the head.
    const head = vrm.humanoid?.getNormalizedBoneNode("head");
    if (head) {
      const p = new THREE.Vector3();
      head.getWorldPosition(p);
      this.camera.position.set(0, p.y, 0.9);
      this.cameraTarget.set(0, p.y, 0);
    }

    this.vrm = vrm;
  }

  setExpression({ emotion, intensity }) {
    const preset = EMOTION_PRESET[emotion] ?? "neutral";
    this.emotion = {};
    for (const p of EMOTION_PRESETS) this.emotion[p] = 0;
    this.emotion[preset] = Math.max(0, Math.min(1, intensity ?? 0.6));
  }

  setViseme({ phoneme }) {
    const preset = VISEME_PRESET[phoneme];
    this.mouth = {};
    if (preset) this.mouth[preset] = 0.85;
  }

  speechEnd() {
    this.mouth = {};
  }

  _animate() {
    const tick = () => {
      const dt = this.clock.getDelta();
      this._update(dt);
      this.camera.lookAt(this.cameraTarget);
      this.renderer.render(this.scene, this.camera);
      requestAnimationFrame(tick);
    };
    tick();
  }

  _update(dt) {
    const vrm = this.vrm;
    if (!vrm) return;
    const em = vrm.expressionManager;
    const k = 1 - Math.pow(0.0001, dt); // frame-rate independent smoothing

    if (em) {
      // Emotions: lerp toward target.
      for (const p of EMOTION_PRESETS) {
        const target = this.emotion[p] ?? 0;
        this.emoNow[p] = lerp(this.emoNow[p] ?? 0, target, k);
        em.setValue(p, this.emoNow[p]);
      }
      // Mouth: lerp toward target, then let the target decay so frames articulate.
      for (const p of MOUTH_PRESETS) {
        const target = this.mouth[p] ?? 0;
        this.mouthNow[p] = lerp(this.mouthNow[p] ?? 0, target, Math.min(1, k * 2));
        em.setValue(p, this.mouthNow[p]);
        this.mouth[p] = lerp(target, 0, Math.min(1, dt * 6));
      }
      // Idle blink.
      this._nextBlink -= dt;
      if (this._nextBlink <= 0) {
        this.blink = 1;
        this._nextBlink = 2.5 + Math.random() * 2.5;
      }
      this.blink = lerp(this.blink, 0, Math.min(1, dt * 12));
      em.setValue("blink", this.blink);
    }

    vrm.update(dt);
  }
}
