---
license: mit
language:
  - en
tags:
  - openenv
  - reinforcement-learning
  - math
  - finance
  - science
  - synthetic
---
# Quantitative Reasoning Lab v1

Built by Leon AI ([github.com/leon-ai/leon](https://github.com/leon-ai/leon)) with Louistiti. Unpublished local experiment.

## Final status: rejected before submission

The capped local proxy solved 20/20 episodes, including all four withheld structures. This fails the predeclared learning-signal gate, so this version was not submitted or trained. No public source repository, Hugging Face dataset or container was created. Source and evidence are retained locally; see `SMOKE.md`. No post-result difficulty tuning or smoke reruns were performed.

## Transfer hypothesis

Practice translating quantitative problems into executable calculations, checking assumptions/units, and reporting complete verified results. This is a focused math/finance/natural-science follow-up to Office v1, which scored 1/40 versus the untrained 4/40. Correct local outputs and training rewards are not evidence of Arena transfer or a ranking improvement.

Sixteen training identities cover integer resource allocation, diagnostic Bayes, finite-population sampling, finite-horizon Markov rewards, directed network routing, fractional-period bond pricing/duration, project after-tax NPV, balloon amortization, money-market/forward FX hedging, constrained minimum-variance portfolios, thermal energy balance, a two-stage decay chain, linear drag dynamics, Arrhenius kinetics, discrete inventory decisions, and overlapping-path reliability. Four additional structures are withheld from the training task list for the capped local test: sequential testing, binomial option pricing, weighted regression and variable-volume tank dilution.

Every reset generates new synthetic parameters, including graph topology, probability distributions and constraints where relevant; explicit seeds are deterministic. These remain 16 authored problem types, not an unlimited generator of novel structures. All data is synthetic, with no actual customer or financial information. `tasks.jsonl` contains one reproducible input preview per training identity, not fixed training examples or target answers. Arena executes only the pinned container, not the dataset.

## Interface and reward

Up to 16 actions per episode: `python` and `submit`. Python executes in a fresh separate process with only numeric/list/dict builtins, math and statistics, including loops, comprehensions and functions. No persistent variables, filesystem/network tools, eval/exec, introspection, classes, numpy/scipy or f-strings. Limits: 3 CPU seconds, 5 wall seconds, 4000 output characters, and 256 MiB worker address space on Linux. AST/capability restrictions plus resource limits are a bounded calculation tool, not a claim of a perfect general-purpose code sandbox. The worker gets only model code, never task or verifier state.

Submit accepts JSON text with finite numeric values, exactly the specified keys. Full reward 1 requires all outputs correct within max(1e-4 absolute, 1e-5 relative). Otherwise reward is 0.15 times fraction of required outputs verified correct, capped below 1. Extra keys, duplicate keys, nonfinite values, booleans and nonnumeric outputs score zero. Formatting/tool use alone earns nothing. Reward is terminal only; no target values or per-key correctness feedback are revealed. No retry within an episode after submission.

## Verification

- 484 local tests passed, including 400 independently computed cases (20 structures x 20 seeds), 20 references executed through the restricted worker, malformed-answer/reward-separation, exploitation/resource, state-isolation and lifecycle tests.
- 32 real network WebSocket reference episodes passed, two seeds per training identity, including no-answer floor reward 0 and independently calculated full reward 1.
- All six runtime checks passed using pinned OpenEnv revision `86a180ede21e044f7929b9a7783ad83aa67d83a3`.
- The fixed 20-episode model smoke completed with full reward on every episode; results and limitations are recorded in `SMOKE.md`. No local training or prolonged tuning.
- GitHub CI workflow templates were prepared to repeat tests in Linux, build a non-root linux/amd64 container, replay all tasks, validate its exact schema and publish immutable-digest reports. They were not run. No container build, publication or anonymous pull was verified.

The prepared Dockerfile copies only runtime modules, manifest and dependencies, not the independent reference solvers, test logs, model runner or credentials. The retained source includes the verifier implementation.

## Reproduce

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest -q test_environment.py
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8768
# Separate terminal:
.venv/bin/python live_replay.py
.venv/bin/openenv validate --url http://127.0.0.1:8768 --level runtime --json
```

The local model smoke runner uses installed Ollama `qwen3.8:27b` as a quantized proxy, not Arena weights or private evaluation. It refuses overwriting its result, fixes 20 single-attempt type/seed pairs before execution, and caps time and tokens. No follow-up tuning based on those results.

Human approval of the exact verified JSON request is required before Arena submission. An accepted/admitted submission starts training automatically; one accepted submission per 24 hours. MIT license; upstream OpenEnv has its separate license.
