# Supplemental audit review: root qualified auditor rejected

The correctness qualification auditor (`correctness-qualification/audit.py`) is acceptable for post-exit execution: it requires exactly28,227 passing ordinary assertions and19 contexts, no measured result output, linked command/process/gate/pins, preserved decoder correction, resource limits and fresh closure including its own process groups. Its supplemental, non-launch-pinned status is explicitly recorded.

Two corrections are required in `audit-qualified.py` before execution. First, its review-binding loop overwrites `p`, the process dictionary, with a path string and later indexes that string as a process record. Rename the binding-loop variable. Second, its final host check adds only the original comparison runner/child to the649-identifier seed; add qualification runner/child PGIDs and SIDs too, covering all653 historical identifiers after qualification.

The qualified auditor otherwise preserves the original failed status and exact111,259 passes/90 known decoder failures, checks the complete2,636-cell/47,448-window/2,674-preparation dataset without removing GC or outliers, and requires both the passing correctness qualification and independent result review. It neither reruns timing nor fabricates the missing original completion marker. This supplemental review does not replace either original launch manifest or the accepted qualification admission. Preserve this rejected auditor revision and bind any corrected revision separately.

No auditor, Julia process or host audit was executed for this static review. Qualification launch admission remains accepted; root cost acceptance remains pending.
