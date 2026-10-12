# V4 publication and Linux verification

Built by Leon AI (https://github.com/leon-ai/leon) with Louistiti.

This record supplements the unchanged historical README/SMOKE evidence. V4 is a submission-ready controlled experiment, **not a demonstrated improvement in training, transfer or ranking**. No Arena submission or training has started. Human approval of the attached exact request is required.

## Public immutable image

`ghcr.io/louistiti/openenv-quantitative-v4@sha256:472393f170dd6319c18fcce2ff0c68b239141eea4944cfd8158d147fcc74b887`

- linux/amd64, non-root user `quant`, default server on port 8000.
- 213,286,382 compressed bytes, 626,329,735 uncompressed bytes, 10 layers.
- The registry manifest digest was independently checked anonymously.
- No assets, secrets, volumes, GPU or downloads are required at runtime.
- Image allowlist: `server.py`, `tasks.py`, `worker.py`, `openenv.yaml`; no oracle, transcripts, tests or tokenizer.

## Verification

Build/source commit: `19766d2`.

Linux CI: https://github.com/louistiti/openenv-quantitative-v4/actions/runs/38191384090

- All 13 frozen v4 source hashes and prior v1/v3 provenance checked unchanged.
- 182 unchanged portable runtime tests passed in 16.24 seconds.
- Container ran with `--cpus=1 --memory=2g` and became healthy in 4 seconds.
- 12 real WebSocket reference episodes and empty-answer floor checks passed across all six generators.
- OpenEnv runtime validation passed 6/6 criteria; action and observation schemas equal the frozen source.

Anonymous CI: https://github.com/louistiti/openenv-quantitative-v4/actions/runs/38191684150

- Empty `DOCKER_CONFIG`; no registry login or package-read credential.
- Pulled the exact immutable digest and ran it with the same resource limits.
- 12 reference/floor episodes, 6/6 runtime criteria and identical schema passed independently.
- Public source access was separately checked without authentication.

The original host-only 199-test suite also passed again (9.27 seconds). Its tokenizer-dependent proxy tests are not claimed portable. Reference/floor replays demonstrate environment correctness, not model performance.

## Exact request for approval

Release: https://github.com/louistiti/openenv-quantitative-v4/releases/tag/quantitative-v4

The release contains 13 verification assets, including `submission-quantitative-v4.json`.

Exact request SHA256: `32ba61cf555dccaed133aef2333a7c92e2ebd72d1c174bcc528332d38802ebd1`.

- Submission ID: `quantitative-reasoning-lab-v4`.
- Two training task IDs only: `constrained-schedule`, `selected-testing`.
- Per episode: 16 actions, 8,192 completion tokens, 24,576 context tokens.
- Reset 120s, rollout 600s, verifier 120s, tool wall limit 120s; 2 GiB RAM, 1 vCPU floor, 1 GiB workspace.
- Exact schema from the tested container. Empty `submit` is both the terminal example action and finish action; it returns zero reward, as verified on every generator.
- Complete numerical correctness earns 1; otherwise independently verified numerical partial credit is capped at 0.15.
- HF dataset omitted because it is optional; all source and evidence are public here. The server generates fresh tasks internally.
- Arena's fixed recipe trains one Qwen3.8-27B policy for at most four hours, then evaluates privately. No longer training is requested.

Local baseline qualification was 5/8 correct on training cases, 3/4 on inspected withheld structures, and 12/12 delivered numeric answers using a quantized local proxy. Those small-screen results establish mixed local success, not Arena-model headroom with certainty or generalization. Judge any eventual run by private evaluation delta, not training reward or job completion.
