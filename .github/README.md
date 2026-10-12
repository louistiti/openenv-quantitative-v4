# Quantitative Reasoning Lab v4

Built by Leon AI ([github.com/leon-ai/leon](https://github.com/leon-ai/leon)) with Louistiti.

The current environment is in [`v4/`](../v4/). It trains fresh-seeded constrained scheduling and conditional inference, sampled uniformly. The calculator, numerical targets, reward tolerances and action interface are frozen from the local qualification screen.

## What is established

- A single predeclared local proxy screen: **5/8 training cases correct**, 3/4 withheld-structure cases correct, and 12/12 numeric answers delivered.
- Both default training families have successes and genuine mathematical failures.
- 199 local tests passed, including preservation and offline screen-interface tests.
- These are capability/headroom checks, **not model learning, Arena equivalence, evaluation improvement or a ranking gain**. The proxy was quantized, the assessment small, and the withheld structures had previously been inspected.
- Linux packaging and publication outcomes are recorded separately in `v4/PUBLICATION.md` when verified.
- No Arena training is authorized until Louistiti approves the exact immutable-image submission request.

## Runtime

```sh
cd v4
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

Default training task IDs: `constrained-schedule`, `selected-testing`. At most 16 actions per episode. `python` executes a fresh bounded numeric calculation; `submit` is terminal. Complete correct numeric answers earn 1. Otherwise, partial numeric credit is capped at 0.15. No targets or per-key correctness are exposed through observations.

The container contains only runtime code and metadata. Reference solvers, tests, screening transcripts and provenance are excluded from it.

## Evidence and historical files

Read [`v4/PROTOCOL.md`](../v4/PROTOCOL.md), [`v4/SMOKE.md`](../v4/SMOKE.md), and the frozen JSON evidence in `v4/`. The original root files are the rejected v1 experiment; `v3/` retains the failed broader v3 gate. They remain byte-identical to support provenance tests. Their historical statements of publication status apply at the time they were written, not to subsequent v4 packaging.

The screening harness requires a private host-local tokenizer and dependencies not included here. Its 199-test host suite is not represented as fully portable. The independent runtime suite and real WebSocket replay are run unchanged on Linux CI.

Do not interpret corrected offline examples, reference replays, high rewards, or successful job completion as model improvement. The next experiment is judged by private evaluation delta.
