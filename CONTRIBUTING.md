# Contributing Guide

## Commit Message Format

Commit subjects must follow conventional commit formatting:
`<type>: <past-tense summary>`

Permitted types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `perf`, `build`, `ci`, `style`, `revert`.
Subjects must be in lowercase, maximum 72 characters, and have no trailing punctuation.

## Git Hooks

Enable local repository hooks:
```bash
git config core.hooksPath .githooks
```
