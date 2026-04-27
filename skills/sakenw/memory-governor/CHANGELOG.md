# Changelog

## 0.2.9 - 2026-04-07

### Added

- `references/dreaming-integration.md` to define how `memory-governor` should coexist with OpenClaw Dreaming

### Changed

- README positioning now explains that `memory-governor` complements Dreaming instead of replacing it
- promotion rules now separate Dreaming-preferred `daily_memory -> long_term_memory` from manual-only hardening paths
- read-order guidance now explicitly excludes `DREAMS.md` from normal startup and recovery reads
- adapter, host-profile, installation, and skill-integration docs now define `DREAMS.md` / `memory/.dreams/` as engine-owned artifacts and keep explicit correction staging out of Dreaming

## 0.2.8 - 2026-04-05

### Added

- `learning_candidates` as a low-commitment target class for corrections and emerging lessons
- `references/correction-pipeline.md` describing the staged correction flow
- fallback template for candidate-layer capture
- checker, validator, and generic host example support for `learning_candidates`
- candidate review workflow documentation and `review-learning-candidates.py` helper
- stronger candidate entry lifecycle guidance, including `lifecycle_stage` and `evidence_count`
- machine-checkable integration checks for host entry files and writer skill contracts
- OpenClaw-style simulated tests covering fallback-only, external-adapter, partial-adapter, and invalid-schema scenarios

### Changed

- explicit corrections now route to `learning_candidates` by default instead of hardening immediately
- promotion rules now describe minimal candidate-to-lesson thresholds
- skill integration docs now explain correction staging and sampling boundaries
- host validation now checks for real `memory-governor` / `Memory Contract` markers instead of file existence only

## 0.2.7 - 2026-04-05

### Added

- maintainer-facing `tests/` with validator, host-checker, and bootstrap coverage
- more complex host fixtures covering split, directory/pattern, unknown target, and missing fallback cases
- `dev/` area for plans and evaluation materials
- `releases/` directory for versioned release notes

### Changed

- repository layout is now clearer about runtime package vs maintainer-only material
- maintainer entry docs are now bilingual in `dev/` and `releases/`

## 0.2.5-beta - 2026-03-31

### Changed

- public README now states more clearly that `memory-governor` is a governance kernel, not an execution-first skill
- public positioning now explains who should use it and when it may feel too heavy

## 0.2.4-beta - 2026-03-31

### Fixed

- `check-memory-host.py` and `validate-memory-frontmatter.py` now support Python 3.9 / 3.10 via `tomli` fallback

### Changed

- installation docs now call out Python version compatibility explicitly

## 0.2.3-beta - 2026-03-31

### Added

- migration guide for hosts that already have a messy memory setup
- manifest examples for `reusable_lessons` as `directory` or `pattern`

### Changed

- host checker and manifest contract now support `fallback_paths`
- installation and integration docs now point legacy hosts to the migration path
- integration checklist now calls out non-single `reusable_lessons` modes explicitly

## 0.2.2-beta - 2026-03-31

### Added

- bilingual public-facing intro sections in `README.md`
- bilingual opening guidance in `SKILL.md`

### Changed

- public packaging now reads more clearly for both English and Chinese readers

## 0.2.1-beta - 2026-03-31

### Added

- clearer English public-facing summary in `README.md`
- bilingual skill description in `SKILL.md` for ClawHub-facing metadata

### Changed

- public packaging now explains the `Installed / Integrated / Validated` model more clearly for external readers

## 0.2.0-beta - 2026-03-31

This is the first distributable beta shape of `memory-governor`.

### Added

- generic core + host profiles packaging model
- packaged fallback templates in `assets/fallbacks/`
- installation and integration guide
- host profile reference for `Generic` and `OpenClaw`
- snippets for host-level and skill-level integration
- before / after comparison page
- generic host validation record
- standalone `examples/generic-host/` example directory
- lightweight bootstrap script for generic hosts
- adapter manifest contract via `memory-governor-host.toml`
- manifest-driven host checker flow for generic and OpenClaw hosts

### Changed

- path-centric design language was tightened into `memory type -> target class -> adapter`
- optional skills such as `self-improving` and `proactivity` are now treated as adapters, not core dependencies
- OpenClaw is now framed as a reference host profile rather than the universal default
- OpenClaw host can now declare its adapter map explicitly instead of relying only on reference-profile inference

### Fixed

- machine-local absolute links were removed from package-facing docs
- fallback assets are now packaged inside the skill
- adapter resolution order is documented explicitly
- host checking can now prefer explicit manifest contracts over directory guessing

### Current Scope

`memory-governor` remains a governance kernel.

It does not attempt to become:

- a second-brain platform
- a universal sync bus
- a forced workspace migration tool

### Known Gaps

- no polished public landing page yet
- no richer installer beyond the lightweight bootstrap
- no versioned release automation
