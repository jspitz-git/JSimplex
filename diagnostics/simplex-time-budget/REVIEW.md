# Independent review

Reviewed by `time_budget_review` after all measurements and metadata completed.
No blocker to committing diagnostic evidence was found.

- All four completed cases have process exit0 and unchanged pins. Available
  modes match status, iteration count, event counters and state/event hashes.
- Exclusive time, allocation bytes/counts and GC reconcile with the root
  counter. Measured compilation is zero; Julia and BLAS use one thread.
- Saved SHA/options independently confirm HH/native160 and prior+256 cleanup
  iteration counts. Direct refactor counters16/9 include projection work not
  fully published as solver events.
- Production src, tests and Project.toml have no diff from fe839aa. No new
  production work, allocations or retained memory are introduced.
- The diagnostic probes, periodic full-state hashing and Profile add real work.
  Reference/census/profile separation, allocation perturbation and GC variation
  are documented. The stalled sampling attempt remains a failed process attempt,
  not a numerical solver result or a successful profile.
- Repeated full-data work is demonstrated, but its numerical redundancy is not.
  The report does not recommend removing safeguards or promise an order-of-
  magnitude speedup. Missing long phaseII, HH-only scope and limited repetitions
  prevent attributing the complete seven-hour run or generalizing percentages.

The reviewer independently parsed the raw reports and metadata and reconciled
all counter totals, rather than relying only on the generated summary.
