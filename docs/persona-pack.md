# Persona Pack spec (v1)

A **Persona Pack** is everything that makes a Komorebi character feel like
*someone* — packaged as a single YAML file so anyone can add a character with one
pull request, no code required. This is the heart of Komorebi's community flywheel:
contributing a persona is the easiest possible first contribution.

## File location & naming

Put the file anywhere under `personas/`. The filename **must** end in
`.persona.yaml`, and the part before that suffix is the persona's **id**:

```
personas/sample/komorebi.persona.yaml   -> id "komorebi"
personas/community/hinata.persona.yaml  -> id "hinata"
```

The id must be unique across the repo and should be lowercase ASCII (it appears in
URLs and the `hello` handshake).

## Schema

| field             | type              | required | meaning                                                        |
|-------------------|-------------------|----------|----------------------------------------------------------------|
| `id`              | string            | yes      | stable identifier; should match the filename                   |
| `name`            | string            | yes      | display name shown in the picker                               |
| `tagline`         | string            | no       | one-line description shown under the name                      |
| `persona_prompt`  | string (multiline)| yes      | the system prompt handed to the LLM; write it *in voice*       |
| `greeting`        | string            | no       | first line spoken automatically on connect                     |
| `voice`           | map               | no       | hints for the TTS backend (see below)                          |
| `expression_bias` | map<emotion,float>| no       | per-emotion intensity multiplier (see below)                   |

### `voice`

Consumed by the active TTS backend; ignored by the `silent` demo backend.

| key            | type   | meaning                                   |
|----------------|--------|-------------------------------------------|
| `backend_hint` | string | which TTS this character prefers          |
| `speaker_id`   | int    | speaker/voice id within that backend      |
| `speed`        | float  | speaking rate multiplier (1.0 = normal)   |
| `pitch`        | float  | pitch shift (0.0 = neutral)               |

### `expression_bias`

The `EmotionEngine` emits an **abstract** emotion + intensity (0..1). The bias map
multiplies the intensity per emotion so two characters react differently to the
same line. Keys are the emotion vocabulary:

```
neutral · joy · sadness · anger · surprise · fear · thinking
```

Example: a stoic character might set `joy: 0.6, anger: 0.5`; an excitable one
`joy: 1.3, surprise: 1.4`. Values are clamped so the final intensity never exceeds
1.0. The wire format stays abstract — bias only tunes *how strongly* this character
emotes, never what the renderer does with it.

## Minimal example

```yaml
id: hinata
name: ヒナタ
tagline: An energetic kid who gets excited about everything.
persona_prompt: |
  You are Hinata, a bright, energetic companion. You speak in short, lively bursts
  and get genuinely excited. You are encouraging and never mean.
greeting: "わー、来てくれたんだ！ねえねえ、今日は何して遊ぶ？"
expression_bias:
  joy: 1.3
  surprise: 1.4
  sadness: 0.8
```

## Checklist before opening a PR

- [ ] Filename ends in `.persona.yaml` and the id is unique & lowercase.
- [ ] `persona_prompt` is written in the character's voice and stays kind.
- [ ] `expression_bias` keys are all from the emotion vocabulary above.
- [ ] The persona shows up in the picker (`GET /personas`) when the server runs.
