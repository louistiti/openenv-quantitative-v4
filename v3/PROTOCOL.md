# Tool and measurement repair diagnostic, frozen before model calls

V2's result is rejected and preserved. V3 changes the calculation interface and local screening fidelity, not tasks, targets, numeric reward, or tolerances. No evidence of training benefit or Arena transfer is claimed.

## Fixed single-attempt worklist

- constrained-schedule: 394101
- leveraged-cashflows: 394102
- selected-testing: 394103
- piecewise-reactor: 394104
- parallel-schedule (withheld): 494101
- american-option (withheld): 494102

One episode per family, in this order. No retries, seed selection, post-result tuning or extension of this diagnostic. It is too small to select a training environment or infer learning headroom. Any later experiment needs its own predeclared protocol and new seeds.

## Caps and controls

Same local qwen3.8:27b tag/digest, nvfp4 MLX proxy, think=false, temperature0.7, context24576. Seed9001+taskseed+step. JSON schema actions and observations; no native action grammar/parser. Concise code/output instruction is new. Six episodes maximum; 300s per episode,1800s total,16actions. Request timeout uses remaining wall time, not an extra80s limit. Wall time is a local resource cap, not an Arena criterion.

No artificial2048-token reply ceiling. Each request uses remaining8192 completion allowance after generated tokens, actual local tokenizer observation tokens and40tokens/turn conservative framing reserve. Initial task/schema are prompt, not completion. Terminal observation is counted too. Oversized observations can exhaust the budget after the action; such episodes are reported as budget failures, not reasoning failures. Local tokenizer/framing are proxies, not proof of Arena exact accounting. Invalid JSON and truncation are distinct outcomes. No repair/retry of invalid model replies.

Tokenizer is taken from the observed Ollama model manifest with SHA2560997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3. Dependency installed into isolated .screen-deps; not part of served environment.

## Acceptance and reporting

Before model calls: all independent/reference/reward/security tests; new numerical imports/nonlocal/error feedback/budget tests; twelve live WebSocket reference episodes and six OpenEnv runtime checks; v1 and v2 preservation hashes; unchanged tasks/reference/reward.

After model calls: report every attempted/unattempted episode, success, delivered wrong answer, calculator error, invalid/truncated reply, wall-time or completion-budget failure separately. A successful candidate is not automatically approved for publishing or training. No submission without fresh exact-request approval.
