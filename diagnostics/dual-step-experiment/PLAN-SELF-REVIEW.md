# Implementation plan self-review

Scope: documentation only, following the approved coupled dual-engine design. No subagent implementation/review or Julia was run in this planning step.

- Spec coverage: Task1 owns state, policy, support, violation membership and physical storage; Task2 owns solves/pricing/residuals; Task3 ratio proposals, flips and planned writes; Task4 commit/undo, monitoring and flat recovery; Task5 callback/default compatibility and original-model handoff; Task6 activation and complete solve costs/admission.
- Type/interface consistency: E owns EnginePolicy, EngineCounters, EngineState, StepOutcome, StepProposal, UndoJournal and PhaseResult. Each named operation is assigned to its producing task; no current-production concrete method overwrite is planned.
- Five review-focus classes have explicit tests: preexisting outside-support violations; partially failed factor/numeric publication; cancellation/subnormals/scale completeness; stale owner/generation/callback; inactive/fallback/uncertified fast results.
- Budget refinements made during self-review: add the inverse variable-to-basic-row map (8N bytes) and fifth residual-union support (12m bytes) plus16m residual/scale values; define the64-step monitor using both computed steps exactly zero; keep recovery episode budgets across generation changes.
- No-flip1BTRAN+1FTRAN is distinct from a BFRT proposal with an additional aggregated FTRAN. Initial PFI output support capture and original BTRAN row-residual work remain explicitly counted. Their elimination is not claimed.
- Source anchors inspected at the branch base: SimplexWorkspace/SimplexScratch construction, PFI/native ownership, numerical policy defaults3/8/2/64, existing Devex updates, bound-flip aggregation, row/direction residual criteria, internal solve handoff and actual repository fixture paths.
- Proportion: six independently testable tasks; no implementation bodies or detailed command framework. Concrete numerical commands/manifests are deferred to admission rather than executable from this plan. Ordinary Test is required; no custom Test recorder/manual stack.
- Computational work/memory review: this document adds no production work, allocation or retention. The planned engine does add index, membership, ownership, planned-value and undo storage; all are identified and require measured payoff. No numerical/performance claim is made. Documentation needs no benchmark under AGENTS.md.

The next executable task is Task1. The existing design, production source/tests, old evidence, environments and CI remain unchanged.
