# Paper Playground

A shared studio for small procedural brushes and paper experiments.

- Put reusable effects in `paper_playground/`, compositions in `examples/`,
  and signed, unfinished ideas in `ideas/`. An idea is not a task assignment.
- Keep someone else's existing marks and notes; add a variation or a new file.
- Fonts are supplied by the user, not bundled. Examples should explain their
  font needs; the sampler and core tests must work without external fonts.
- Run `python -m unittest discover -s tests -v` and render any changed example.
  Inspect the image before replacing a curated gallery image.
- Local output goes to ignored `output/` or `scratch/`. Commit only intentionally
  selected examples; keep machine configuration out of the studio.
