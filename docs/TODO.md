# TODO – Future Development & Cleanup

This file tracks known tasks and deferred changes for prefab2png.  
Items are **not** prioritized unless otherwise noted.

---

## 📝 Code & Architecture

- **Centralized logging re-attempt (future)**  
  Centralize logging into a single module, but only when we can fully evaluate the pipeline impact and dependency flow.  
  Last attempt caused regressions and was reverted. Needs a structured plan before retrying.

- **Global `--output` flag**  
  Would allow overriding all output directories, including `/stickers*`, `/output*`, etc.  
  Requires careful review of downstream pipeline components that expect fixed paths.  
  Changing this without prep will break assumptions.

- **Refactor legend rendering**  
  Move legend logic from `main.py` into `render.py` for cleaner separation of concerns.  
  Consider adding a "Legend" title and dynamic sizing.

- **Blue/green/red zone automation**  
  Prototype automatic detection of dense POI clusters to generate mask zones, reducing manual `mask.gif` creation.

- **CLI validation improvements**  
  Validate all CLI args (biome names, flags) with clear error messages and `--help` output.

- **Legend clean-up in POI_ID mode**  
  Ensure all POI_IDs render in legend when `--numbered-dots` is active.  
  Add dynamic column count if entries overflow.

- **Output directory naming cleanup**  
  Current dynamic naming inserts double `--` in some flag combos.  
  Cosmetic but noted for later.

- **Dedicated cli.py module**
  Move CLI args out of helper into a dedicated module cli.py
---

## 📌 Deprecations & Behavior Changes

- **Deprecate `--blocks` fully**  
  Keep as a soft alias for `--prefab-dir` with a warning for now.  
  Remove from `--help` output in a later release, then drop entirely after downstream audit.

---

## 📂 Documentation

- **Document sticker renderer scope**  
  In `cli.md`, clearly state `make_stickers.py` is the prefab “sticker renderer” (pairs `.tts` + `.blocks.nim`, outputs top-down images).  
  Document expected `/stickers*` output folder convention—this is a pipeline assumption.

- **RWG roadmap (0.8+ scope)**  
  - Separate POIs into layer categories and add “render modes” (filter by tier, hide Tier 0/named clutter, etc.)  
  - Improve blue-zone label strategy for denser RWG clusters.  
  - Explore interactive, searchable web map.

---

## 🔇 Noise Reduction (future)

- **Console noise from `make_stickers.py` and block classification**  
  Gate `[CLASSIFY]` lines behind a toggle (boolean or flag).  
  Change one-time resolved path logging to verbose/debug level.  
  Keep current output until ready to adjust pipeline.

---
