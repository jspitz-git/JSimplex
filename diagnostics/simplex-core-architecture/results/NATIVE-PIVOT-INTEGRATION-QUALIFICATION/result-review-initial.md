Initial diagnostic review finding (preserved)

REPORT.md groups both durations as including termination. guard.py records elapsed_including_launch before stop_owned cleanup; only the outer invocation elapsed includes termination. Clarify the inner value as elapsed at cleanup entry.

The numerical attempt remains FAILED/CONSUMED regardless of this reporting clarification. No evidence, driver, settings, or execution changes are requested.
