# Ownership fix after independently observed RED

Initial GREEN admission rejected before any GREEN launch: public basis_matrix(source) called a validator that writes source.scratch.basic_mask. A separate admitted ordinary one-assert regression dirtied that mask and failed exactly once,0errors/exit1 in9.308s; all140pins matched at exit. Original rejected136pin source/review and ownership-RED140pin code/raw remain preserved.

Fix: validate into the already-required owned N-entry inverse map without writing source state, then call the unchanged owned-assembly helper directly. Reuse that inverse in initial membership; no additional temporary full mask or repeated copied-basis scan. Public rebuild uses the same owned validator. Numeric dimensions are checked before reading fields. Main GREEN snapshot now includes basic_mask and dirties it before import, covering the actual failure in the full suite.

ownership-before-map.json maps changed old source/test bindings to exact preserved copies by hash; these are historical read/launch bindings, not current-file claims. No old numerical script is rerun. Full GREEN has new green-final-pins.json and run-green-final.py. All original expectations remain, with the source-mask regression strengthened. No production/test/env/CI change, no user tolerance change, no benchmark.
