# MA-N publication amendment

The initial publication gate returned FALSE and stopped before commit/push.
`git diff --cached --check` identifies exactly a single-space line 15 in each of
frozen prepare-2.py and prepare-3.py. Both were already read-time pinned and
independently reviewed. They are preserved byte-for-byte, as are the initial
publication failure and original PASS closure. The original unstaged diff check
did not cover newly staged files; it is not evidence that their whitespace was clean.

A separate supplement binds and verifies those exact two diagnostics and original
hashes. Final publication must reject any additional diagnostic, verify all initial
bindings, require independent amendment acceptance and a separate PASS closure,
and freeze the complete expanded staged name/blob list before commit/push.
No candidate, numerical code, assertions, inputs or original evidence is changed.
