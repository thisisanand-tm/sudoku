# Application separation - 20 September 2026

This repository's `main` branch once again contains the original Sudoku game.

- Sudoku: https://thisisanand-tm.github.io/sudoku/
- Examination test: https://thisisanand-tm.github.io/iica-examination/
- Examination repository: https://github.com/thisisanand-tm/iica-examination

The full exam snapshot (87 source files and the unchanged 501-question bank) has been migrated to the examination repository. The former exam branch is retained as `backup-exam-before-migration-20260920` for recovery.

Sudoku game logic was restored from commit `9029c43b54caf9dc4645d9115b2e4bb71783c011`. The invalid legacy web manifest was repaired and offline registration reconnected. The restoration check in `restoration-validation.json` confirms the inline game logic is unchanged.

No browser localStorage is cleared by this migration. Cache cleanup is limited to old Sudoku caches and the former exam cache names; the new IICA examination caches are separate.
