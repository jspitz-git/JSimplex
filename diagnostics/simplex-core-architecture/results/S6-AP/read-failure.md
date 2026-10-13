# Initial attachment read limitation

The first sandbox exec attempt to read the attachment failed before process creation:
`Failed to create unified exec process: No such file or directory (os error 2)`.
The subsequent explicitly escalated /bin/bash read succeeded. No script or Julia
ran in the failed attempt; no automatic approval rejection occurred.
