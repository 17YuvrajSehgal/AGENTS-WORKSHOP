# Labelling instructions (perf PR check)

You get one file: `sheet_<your id>.xlsx`, 300 pull requests. The other
labeller has the same PRs in a different order.

1. Read `labels/codebook-perf-v0.md` first. It is the only rulebook.
2. For each row, read the title, description, commit messages and changed
   files. Open the PR link only if the text is not enough, and write
   "opened link" in `notes` when you do.
3. Fill the four answer columns using the drop-down lists:
   `perf_role`, `perf_scope`, `confidence`, and type `evidence_quote`
   (copy the exact sentence from the PR; leave it empty when the role is
   `none`).
4. Work alone. Do not discuss PRs with the other labeller until both
   sheets are finished. Disagreements are part of the measurement.
5. Do not look at any machine labels (`key.csv` is not for labellers).
6. A `□` in the text marks an invisible control character from the
   original PR.

Expected time: about 1 to 2 minutes per PR (5 to 10 hours in total).
Send the finished sheet back as `sheet_<your id>.xlsx`, unchanged
otherwise.
