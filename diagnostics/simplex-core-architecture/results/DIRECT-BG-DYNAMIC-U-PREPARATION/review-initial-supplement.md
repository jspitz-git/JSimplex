# Initial review supplement — publication membership

This supplement preserves review-initial.md/json unchanged. The author identified a further publication gate concern immediately after the initial review was saved; independent inspection confirms it.

## I3 — Important: reject new files introduced after closure

`publication.py` verifies every closure hash but then derives staged names from a fresh recursive evidence-directory scan. A new file added after closure can therefore enter publication without appearing in closure.sha256 or the accepted review. Before creating publication-names.json/publication.json or mutating the index, require exact equality between the actual complete prepublication artifact set (evidence directory, candidate files, both continuation files) and the closure.sha256 keys plus closure.json. Then derive the staged set from that bound membership. This is an offline evidence-integrity issue; it does not imply a Julia execution or numerical finding.

The initial review and this supplement jointly form the complete findings before the single author amendment: I1 growth prefix initialization, I2 descriptive check count, I3 prepublication membership. Final review must inspect the amended implementation, success oracle, manifest, canonical selections, closure/publication scripts and reconciled prior hashes.
