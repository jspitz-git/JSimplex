# Additional cold shape admission

No Julia launched. Original94pin draft preserved unexecuted. Canonical new driver-2.jl includes replay-core-2.jl. Only additions to interval replay: COLD checks of every logical U row<=column and every finite/nonzero diagonal on every update, saved as explicit trace fields before acceptance. Extra full index scan and n diagonal searches are cold, outside hot timing. Important because shortening BG region must never leave a subdiagonal element. Existing component shape/copy/input checks and independent fullcold residuals remain unchanged. No productionmethodoverwrite.

Canonical one run: python3 -B run.py local-1 command-2.json pins-2.json1800 0 after independent acceptance. Same32cold+32warm+160measured/budget/guards1800s. Entire timing run rejects any failure. No outputs exist.
