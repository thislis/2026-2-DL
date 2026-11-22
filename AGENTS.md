# Repository Guidelines

## Project Structure

This repository contains the proposal and implementation plan for predicting Spotify track popularity, explaining predictions by genre, and suggesting feasible changes to a track.

- `README.md` identifies the course repository.
- `docs/project-overview.md` is the Korean-language project guide. Consult it for research questions, model comparisons, and the evaluation protocol.
- `docs/prepare/proposal_music_popularity_xai-1.pdf` is the original proposal. Cite its page number when referring to a proposed experiment or benchmark.
- `docs/history.md` records completed work. After each task, append a dated entry summarizing what changed, how you did it, and why. One or two sentences are enough.

The PoC CLI lives in `src/music_popularity/`. Dataset and model settings live in `configs/`; local data and run artifacts are ignored by Git.

## Version Documentation

Keep the root README focused on the project purpose, shared directory layout, repository-wide conventions, and links to version documents. For each version, create or reuse `docs/<version>/` (for example, `docs/PoC/`). Write setup and run commands in a run guide there. Document version-specific features, model architecture, and planned changes in separate topic files as needed. Link new guides from the README’s version index and label planned workflows clearly.

## Development and Validation

Keep validation proportional to the change. Choose the smallest check that covers the affected behavior. Broaden the checks only if the change affects other components or a focused check reveals a problem. For documentation edits, choose from these commands as needed.

- `rg --files docs` lists project documents and assets. Use it to check the spelling and capitalization of link targets.
- `git diff --check` checks unstaged changes to tracked files for whitespace errors. After staging files, run `git diff --cached --check` to include new documents.
- `git status --short` lists modified and untracked files for review before committing.

Preview Markdown when changing its layout and follow any links you add or edit. Use the relevant version’s run guide for setup and test commands.

## Writing and Experiment Conventions

Match the language of the document you edit. Use descriptive Markdown headings, blank lines between paragraphs, and lowercase hyphenated filenames such as `project-overview.md`. Link to repository files using relative paths.

Distinguish published benchmarks, illustrative advice cards, and measured results. For a model comparison, report the dataset version, input columns, split procedure, and evaluation metrics. Verify the feature count against the CSV header before implementing the input schema.

## Commits and Pull Requests

Git history contains only `Initial commit`, so a commit convention has yet to emerge. Use a short imperative subject such as `Document genre-level evaluation`. In a pull request, describe the change, identify the affected document or experiment, and list the checks performed. Link the relevant issue when one exists.
