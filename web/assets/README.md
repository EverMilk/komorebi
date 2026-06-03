# Avatar models

Drop a VRM model here as `avatar.vrm` to use the 3D renderer:

```
web/assets/avatar.vrm
```

Then open the demo with the VRM renderer selected:

```
http://localhost:8000/?renderer=vrm
```

Or point at any URL without copying a file:

```
http://localhost:8000/?renderer=vrm&vrm=https://example.com/model.vrm
```

**Models are not committed to this repo.** VRM models carry their own licenses
(often non-MIT), so `*.vrm` is gitignored. Bring your own model — for example one
you create/export, or a CC0 / explicitly-redistributable model. Always check the
model's license before sharing a deployment. See `docs/avatar-renderers.md`.
