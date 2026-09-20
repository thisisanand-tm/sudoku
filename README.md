# Sudoku

The original Sudoku game, restored from commit `9029c43b54caf9dc4645d9115b2e4bb71783c011`.

Play: https://thisisanand-tm.github.io/sudoku/

The Independent Director examination application has moved to the dedicated repository https://github.com/thisisanand-tm/iica-examination and its intended site https://thisisanand-tm.github.io/iica-examination/.

The complete pre-migration exam source is also retained in the `backup-exam-before-migration-20260920` branch for recovery. This repository's main branch serves Sudoku, not the exam application.

The service worker uses a Sudoku-specific cache, removes obsolete exam caches from the old Sudoku path, and never clears browser localStorage or the new IICA application's caches.
