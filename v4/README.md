# Quantitative reasoning lab v4: narrowed local candidate

Default training sampling is uniform between constrained scheduling and selected conditional inference. Generators, numeric targets, reward tolerances, calculator, action schema and system prompt are unchanged from v3. Finance and reactor families remain explicitly resettable legacy development cases, excluded from default sampling. Parallel scheduling and American option families remain explicitly selected validation structures, not default training.

Why narrow: v3's broad 20-case gate failed with 16/20 usable answers. Scheduling and conditional inference had mixed successes and failures with reliable delivery; finance and physics had no fully correct answers and multiple nondelivery outcomes. V4 is a NEW predeclared fresh-case screen, not a retroactive relaxation of v3's gate.

Read PROTOCOL.md and SMOKE.md before using this candidate. The fixed 12-case local gate passed: 5/8 training correct, 3/4 validation correct, 12/12 usable answers. This is neither model learning nor evidence of Arena ranking improvement. No publication, submission or training has occurred. Linux container validation remains blocked locally because Docker CLI is unavailable.

## Runtime

Python 3.11 with requirements.txt. Run `uvicorn server:app --host 0.0.0.0 --port 8000`. OpenEnv session actions support bounded fresh-process Python calculations and one terminal numeric JSON answer. No oracle or per-key correctness feedback is returned to the agent. Full numeric correctness earns 1; otherwise numeric partial credit is capped at 0.15. Maximum 16 actions.

`pytest -q test_environment.py test_candidate.py test_screen_interface.py` was run from the original isolated workspace with its parent v1/v3 preservation fixtures. Those provenance tests intentionally depend on the original workspace; this archive is not a standalone reproduction of the entire earlier history. Live reference replay and runtime validation were also completed in that workspace.

## Frozen evidence

candidate-freeze.json contains source hashes, model digest, worklist and pre-screen runtime checks. model-smoke.json contains original transcripts. candidate-gate.json records the unchanged qualification decision. candidate-audit.json independently checks answers and token accounting. failure-mechanisms.json contains OFFLINE corrections only. diagnostic-freeze.json is a copied v3 provenance artifact, unused by the v4 screen.

smoke_model.py and qualify_model.py refuse existing outputs: do not delete evidence to rerun these seeds. The screening harness uses private host-local tokenizer weights and tokenizers dependencies that are intentionally not included in the archive. Its execution should not be claimed portable without those prerequisites. The server itself does not require the screening tokenizer or model.

## Recommended next experiment

Use this frozen two-family curriculum for a modest controlled Arena training run only after Linux packaging/runtime validation and explicit approval of the exact training request. Keep training seeds separate from a predeclared assessment set. Compare the same evaluator before and after training; inspect valid-episode rates and delivery failures separately from mathematical errors. Judge success by evaluation delta, not training reward or job completion. Do not widen or scale this curriculum until transfer improves.
