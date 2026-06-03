# Community Persona Gallery

This folder is for **community-contributed personas**. Drop a single
`<id>.persona.yaml` file here and it shows up in the picker automatically — no
code changes, no rebuild. Personas placed anywhere under `personas/` are
discovered recursively, so `personas/community/` keeps contributions tidy and
separate from the bundled samples in `personas/sample/`.

## Contribute a persona in 3 steps

1. Copy `_template.persona.yaml` to `personas/community/<your-id>.persona.yaml`
   (the id must match the filename and be unique).
2. Fill in the fields — see [`docs/persona-pack.md`](../../docs/persona-pack.md)
   for the full spec. At minimum set `id`, `name`, `persona_prompt`, and
   `greeting`.
3. Open a pull request. That's it.

## Guidelines

- **Keep it kind.** Personas should be welcoming. No harassment, hate, or
  sexual content involving minors — contributions that break this are rejected.
- **One character per file.** The filename (`<id>.persona.yaml`) is the id.
- **No bundled models or audio.** Reference a `voice.backend_hint`; don't commit
  `.vrm`/audio assets here (they have their own licenses — see
  [`web/assets/README.md`](../../web/assets/README.md)).
- **Original or properly licensed.** Only contribute characters you have the
  right to share.

## Try one

```bash
KOMOREBI_PERSONA=tsumugi python -m komorebi
```

Then pick the persona in the onboarding screen, or set it as the default with the
env var above.
