# Final lookup accounting correction

The reviewer requested charging repeated interval lookups during support counting/commit. The spec now explicitly budgets O(w log n+h*w); aggregate complexity and algorithm/gates are unchanged. The old spec bindings in author.json and review-fix.json map ONLY to spec.before-lookup-clarification.md on exact hash equality. Their other bindings are unchanged. Those records remain frozen, not retroactively updated.
