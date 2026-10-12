# Completed six-family repair diagnostic

Frozen result SHA256: a74a3d83f8ca551dfab32188202c47ea8e7c184bc718a8d8019981ef3e8a480d.

All six planned episodes attempted. Two correct submitted answers, four wrong submitted answers. No timeouts, token-budget failures, invalid JSON or truncated replies. Five recoverable calculator errors, all on withheld structures. Process exited0. Independent reference and transcript token-ledger audit passed for all six.

| Family / seed | Outcome | Seconds | Accounted completion | Worker errors |
| --- | --- | --- | --- | --- |
| constrained-schedule394101 | correct |30.38|1437|0|
| leveraged-cashflows394102 | wrong |77.72|4987|0|
| selected-testing394103 | wrong |37.55|1679|0|
| piecewise-reactor394104 | wrong |45.31|2025|0|
| parallel-schedule494101 withheld | correct |77.89|2994|4|
| american-option494102 withheld | wrong |33.60|1206|1|

## Confirmed failures worth investigating

Offline counterfactual corrections to the submitted programs recover every independently computed answer key for the three failed training families. These were human-agent analysis checks, not model retries or added model successes. Tasks/reward/harness have not been tuned to these seeds.

- Finance: funded initial reserve omitted from opening cash; existing loss carry double-counted on negative taxable income; salvage taxed separately without using tax-loss carry.
- Conditional inference: used P(Z=1) for both binary latent states, rather than P(Z=0)=1-P(Z=1).
- Physical model: B production term absent and outflow sign wrong; omitted continuous B discharge; failed to restore volume during equal-volume drain/refill.
- Withheld option pricing: independently computed prices and premium disagree with all three submitted keys. No counterfactual correction or task tuning performed.

This is more informative than v2 resource failures, but not a controlled causal comparison: seeds are different and both tools and screening fidelity changed. One seed per family cannot establish recurrence, trainability or Arena transfer.

## Next bounded evidence

GENERALIZATION_PROTOCOL.md fixes20fresh episodes with four seeds per training family and two per withheld family, interleaved. Same tested prompt/calculator/accounting. The gate is frozen before model calls. A local pass would justify a candidate for further controlled training evaluation, not a claim of ranking improvement or permission to submit.
