# V3 recurrent-headroom qualification screen, frozen before calls

The six-case diagnostic is preserved:2successes,4wronganswers,0time/budget/replyfailures. Its seeds are never repeated. Tasks/reward/schema/system prompt/calculator/accounting remain unchanged. This screen tests recurrence, not training or Arena ranking improvement.

## Worklist and caps

Four rounds. Each round has constrained-schedule,leveraged-cashflows,selected-testing,piecewise-reactor in that order, with seed594101+10*round+family_index. After rounds0and1 append parallel-schedule,american-option with seeds694101+10*round+heldout_index. This fixed interleaving protects withheld coverage against the global cap. Exactly20planned single attempts. No retries, cherry-picked seeds or post-result extensions.

Same local qwen3.8:27b nvfp4 MLX proxy/digest and frozen smoke_model.py, thinkfalse,temp0.7,context24576,16actions,300s/episode,1800s total,8192accountedcompletion. No2048reply or80srequestlimit. Token accounting remains a local proxy, not Arena-exact. Generalization wrapper changes only worklist/output destination; original frozen diagnostic harness hashes are checked, plus new protocol/wrapper/diagnostic result preservation hashes.

## Predeclared qualification gate

All20attempted;4through14of16training episodes solved;atleast2trainingfamilies have both successes and nonsuccesses;atleast1of4withheld solved;atleast18of20episodes deliver a numeric answer with outcome success or wrong_answer and fit the completion budget. Infrastructure outcomes and unattempted episodes are reported separately, not evidence of reasoning difficulty. Gate failure means no submission from this screen, not silent retuning.

A passed local gate qualifies a candidate for further controlled training evaluation. It does not establish trainability, learning gains or Arena transfer. Future work must preserve this result, use a new protocol and require exact-request approval before submission/training. No private evaluation questions accessed. Offline corrections are not model successes or added training examples.
