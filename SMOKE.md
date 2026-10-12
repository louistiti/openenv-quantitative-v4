# Capped model smoke test: candidate rejected

Run: 2026-10-11. Decision: do not publish or submit this version for Arena training. The predeclared gate rejects an all-success or all-failure smoke run, or exploitable reward. This run had 20/20 full-reward outcomes, including all four withheld structures, and therefore failed the learning-signal gate. No difficulty changes, reruns, local training, Arena submission or private evaluation followed.

## Protocol

Local Ollama tag `qwen3.8:27b`, observed as a 27.8B qwen3_5 model with nvfp4 safetensors and MLX runner, without a custom system prompt. This is a quantized local proxy, not Arena weights. The test used the JSON action schema/system prompt and JSON user observations, without native tool calls or a grammar-constrained response format. The model received task inputs/instructions, not target values or reference solvers.

The fixed worklist contained one episode per training type and four withheld types, with seeds 86713 through 86732. Caps: 20 episodes, 1200 seconds overall, 120 seconds and 8192 generated tokens per episode, 16 actions. Temperature 0.7, thinking disabled, context 24576, per-response output limit 2048. Each type/seed was attempted once; calculation errors could be corrected within the episode's fixed action budget, but terminal submissions could not be retried. Complete transcripts are in `model-smoke.json` and contain synthetic tasks only.

## Results

Every episode ended normally with reward 1 and no episode error. Process exit code: 0. Total: 57 actions, 16226 generated tokens, 453.44 seconds summed episode time. The final aggregate reported `mixed_outcomes: false` and `heldout_solved: 4`.

| Type | Seed | Withheld | Actions | Tokens | Seconds | Reward |
| --- | --- | --- | --- | --- | --- | --- |
| resource-allocation | 86713 | no | 4 | 563 | 16.38 | 1 |
| diagnostic-bayes | 86714 | no | 4 | 1294 | 30.81 | 1 |
| finite-sampling | 86715 | no | 4 | 879 | 21.07 | 1 |
| markov-rewards | 86716 | no | 3 | 1096 | 25.47 | 1 |
| network-routing | 86717 | no | 5 | 1553 | 37.77 | 1 |
| bond-cashflows | 86718 | no | 2 | 572 | 16.58 | 1 |
| project-after-tax | 86719 | no | 3 | 1032 | 25.64 | 1 |
| loan-balloon | 86720 | no | 3 | 900 | 26.16 | 1 |
| currency-hedge | 86721 | no | 3 | 749 | 19.77 | 1 |
| portfolio-risk | 86722 | no | 2 | 559 | 16.27 | 1 |
| thermal-balance | 86723 | no | 2 | 543 | 16.05 | 1 |
| decay-chain | 86724 | no | 2 | 342 | 10.27 | 1 |
| fall-with-drag | 86725 | no | 3 | 603 | 18.33 | 1 |
| reaction-temperature | 86726 | no | 2 | 322 | 10.59 | 1 |
| inventory-decision | 86727 | no | 2 | 426 | 13.38 | 1 |
| network-reliability | 86728 | no | 4 | 1819 | 52.34 | 1 |
| sequential-testing | 86729 | yes | 2 | 324 | 10.25 | 1 |
| binomial-option | 86730 | yes | 2 | 272 | 10.57 | 1 |
| weighted-regression | 86731 | yes | 2 | 553 | 18.19 | 1 |
| tank-dilution | 86732 | yes | 3 | 1825 | 57.55 | 1 |

## What this establishes

The proxy can complete these authored quantitative structures through the calculation interface, sometimes recovering from tool/calculation errors before submitting. It does not establish training improvement, broad generalization, private grading performance or leaderboard gains. One seed per type is a small screening sample; four withheld authored structures are not a comprehensive independent benchmark. All-success outcomes suggest saturation in this sample, not proof that every Arena rollout would succeed or that training gradients are universally zero.

The environment separately passed 484 local tests, 32 real WebSocket reference episodes and six pinned OpenEnv runtime checks. Those validate local correctness and integration, not transfer. Linux/amd64 container builds, anonymous pulls and CI workflows were prepared but never executed. No public source repository, Hugging Face dataset or container was created for this rejected candidate. The source and evidence are retained locally.
