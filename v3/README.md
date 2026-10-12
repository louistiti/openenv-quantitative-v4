# Quantitative workbench v3: tool/measurement repair

Local diagnostic only. No public container, submission or training. Ranking improvement has not been demonstrated.

V1 remains rejected (20/20 small local formula-led successes). V2 remains rejected: 17/20 fixed attempts, three successful selected-testing episodes, eleven timeouts and three artificially truncated replies; three withheld episodes not attempted. Its frozen screen is not a usable selection test. V3 preserves v1 and v2 and changes only numerical tool support, feedback and screening fidelity.

## Intentional changes

- Calculator adds numerical itertools and nonlocal syntax, retaining restricted imports/private names, fresh subprocess per action, CPU/output/code limits and no filesystem/network tools.
- Tool errors include a bounded240-character message, not a traceback or source context. This is a capability-restricted calculation process, not a general-purpose untrusted-code sandbox guarantee.
- Action/schema prompt requests concise calculations and output. It does not reveal reference solutions.
- Local screen removes artificial2048reply and80secondrequest limits. Requests use remaining8192completion allowance, counting actual local-tokenizer observations and40framing-reserve tokens/turn. This remains a local proxy for Arena tokenizer/runner.
- Same tasks, targets, reference solvers, reward function, tolerances and proxy model digest as v2. Fresh seeds rather than tuning v2 cases.

## Evidence and boundaries

201 independent/reference/reward/security/budget tests passed;12live WebSocket reference episodes and6OpenEnv runtime criteria passed. Six further offline synthetic-reply tests passed. The six-family model diagnostic is fixed by PROTOCOL.md and diagnostic-freeze.json. Completion requires inspecting its terminal results; no claim of learning headroom from infrastructure failures or a six-seed sample.

No Linux container validation has been performed. No private Arena evaluation questions or traces were accessed. Quantized local Qwen success/failure is not evidence of Arena training transfer. Publication or training requires a separately justified candidate and fresh approval of the exact submission request.

## Reproduce reliability checks, not model reruns

From this directory:

    ../.venv/bin/python -m pytest -q test_environment.py test_repairs.py test_screen_interface.py
    ../.venv/bin/python -m compileall -q tasks.py worker.py server.py reference.py budget.py smoke_model.py

WebSocket replay writes replay-local.json and refuses to overwrite existing evidence. smoke_model.py likewise refuses an occupied model-smoke.json and verifies frozen source hashes. Do not delete frozen results to rerun. The tokenizer dependency .screen-deps is isolated from the served environment and is not a deployment requirement.
