# Avatar renderers

An avatar renderer turns the core's **normalized** events into a moving character.
It implements `web/src/avatar/AvatarBackend.js` and receives only abstract
`expression` (emotion + intensity) and `viseme` (mouth phoneme) events — it never
learns which LLM or TTS produced them. That indirection is what lets one core drive
any face.

| renderer      | file                              | deps         | needs a model |
|---------------|-----------------------------------|--------------|---------------|
| `placeholder` | `avatar/PlaceholderAvatar.js`     | none         | no            |
| `vrm`         | `avatar/VrmAvatar.js`             | three, three-vrm (CDN) | yes (.vrm) |

## Selecting a renderer

The renderer is chosen by URL query parameter (default `placeholder`):

```
http://localhost:8000/                       # placeholder (2D canvas face)
http://localhost:8000/?renderer=vrm          # 3D VRM, model from /assets/avatar.vrm
http://localhost:8000/?renderer=vrm&vrm=URL  # 3D VRM, model from an explicit URL
```

If the VRM renderer can't initialize (no model, network/WebGL error), the app
**falls back to the placeholder** so the demo always works.

## Using the VRM renderer

1. Get a `.vrm` model (see licensing below) and either:
   - copy it to `web/assets/avatar.vrm`, or
   - host it somewhere and pass `?vrm=<url>`.
2. Open `http://localhost:8000/?renderer=vrm`.

`three` and `@pixiv/three-vrm` load from a CDN via the importmap in `index.html`,
and only when the VRM renderer is selected — placeholder users download nothing
extra. (The CDN pins are swapped for bundled deps in the M2 TS + Vite migration.)

### How events map to a VRM

| core event              | VRM expression preset                         |
|-------------------------|-----------------------------------------------|
| `joy`                   | `happy`                                        |
| `sadness` / `fear`      | `sad`                                          |
| `anger`                 | `angry`                                        |
| `surprise`              | `surprised`                                     |
| `thinking`              | `relaxed`                                       |
| `neutral`               | `neutral`                                       |
| viseme `a/i/u/e/o`      | mouth `aa/ih/ou/ee/oh`                          |

The `intensity` (0..1) sets the preset weight. Weights are lerped each frame for
smooth transitions, the mouth decays between visemes to read as articulation, and
idle blinking + camera eye-contact run automatically.

## Model licensing (important)

**Komorebi bundles no models.** VRM models almost always carry their own license
terms (redistribution, commercial use, modification, violent/sexual use clauses).
`*.vrm` is gitignored on purpose. Before you commit a model or ship a public
deployment, confirm the model's license permits it. For sharing a ready-to-run
demo, prefer a CC0 or explicitly-redistributable model, or one you created.

This is also why the **core stays MIT-clean**: the optional Live2D renderer (a
later addition) will depend on the Live2D Cubism SDK, which has its own commercial
license, so it ships as a separate opt-in plugin — never a core dependency.

## Writing your own renderer

Implement the interface and you're done:

```js
import { AvatarBackend } from "./AvatarBackend.js";

export class MyAvatar extends AvatarBackend {
  mount(canvas) { /* set up your drawing surface */ }
  setExpression({ emotion, intensity }) { /* drive the face */ }
  setViseme({ phoneme }) { /* drive the mouth */ }
  speechStart() {}
  speechEnd() {}
}
```

Then register it in `main.js`'s renderer selection. See `PlaceholderAvatar.js`
(2D, no deps) and `VrmAvatar.js` (3D) as the two reference implementations.
