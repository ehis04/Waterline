# AGENTS.md — rules for AI coding agents in this repository

Read this file at the start of every session. It overrides your default habits. If an instruction here conflicts with a task request, ask before acting.

## 1. Commits, PRs and authorship (non-negotiable)

**Format:** `<type>: <past-tense summary>`. Lowercase. No trailing full stop. Subject ≤ 72 characters.

| Type | Use for | Example |
|---|---|---|
| `feat` | New user-facing capability | `feat: implemented fund overlap matrix` |
| `fix` | Bug in product behaviour | `fix: fixed var sign error on negative returns` |
| `chore` | Maintenance, tooling, config, deps, small non-product fixes | `chore: fixed broken ruff config bug` |
| `refactor` | Code change with no behaviour change | `refactor: extracted ledger fold into module` |
| `test` | Tests only | `test: added property tests for look-through sums` |
| `docs` | Docs, ADRs, comments | `docs: added adr for quantile convention` |
| `perf` | Performance | `perf: vectorised historical var loop` |
| `build` / `ci` | Build system / pipelines | `ci: added nightly eval workflow` |

- Optional scope: `feat(lookthrough): implemented residual buckets`.
- Optional body after a blank line: *why* the change was made, wrapped at 72 characters.
- One logical change per commit. Never mix a refactor with a feature.

**Never reference an AI, agent, model or tool anywhere in the repository history or code.** This means:
- No `Co-authored-by:` trailers. No `Generated with …`. No session links. No robot emoji. No `noreply@anthropic.com` or similar addresses.
- No mention of Claude, ChatGPT, Copilot, Cursor, "AI", "agent" or "assistant" as an author in commit messages, PR titles or descriptions, code comments, docstrings, changelogs or file headers.
- Do not change `git config user.name` or `user.email`. Commits use the repository owner's identity.
- Never pass `--no-verify`. The hooks in `.githooks/` enforce these rules; if a hook rejects a commit, fix the message and retry.
- PR descriptions contain: summary, why, how it was tested, risks. Nothing else.

(Mentions of AI *as a product feature*, e.g. `feat: implemented import mapping assistant`, are fine. The rule is about authorship.)

## 2. Git workflow

- Branch per issue: `feat/<ticket-id>-short-name`, `fix/<ticket-id>-short-name`. Never commit directly to `main`.
- Commit when a unit of work passes its tests. Do not push, merge, force-push, rebase shared branches, or delete branches unless asked.
- Never rewrite or amend commits you did not create in this session.
- Before committing: `git status -s` and `git diff --stat`; stage files explicitly (no `git add -A` unless every change is intended).

## 3. Working efficiently (token and time budget)

Context is the scarcest resource. Every file you read and every line of command output stays in context and costs money and accuracy.

**Find before you read**
- Search first: `rg -n "symbol" packages/` or `rg -l` to list files. Read only the lines you need (use offsets/line ranges).
- The product spec (`docs/spec/*.md`) is long. Never read it whole. `rg -n "^#{1,3} " docs/spec/<file>.md` to list headings, then read only the section the task names.
- Never open: `node_modules/`, `.venv/`, `dist/`, `build/`, `coverage/`, lockfiles (`uv.lock`, `pnpm-lock.yaml`), generated clients (`packages/api_client/`), `data/` contents, minified files. For data files use `head -n 5` and `wc -l`.
- Do not re-read a file you just wrote or edited; your edit is the current state.

**Keep output small**
- Use quiet flags: `pytest -q -x`, `ruff check --quiet`, `pnpm -s`.
- Truncate long output: `… 2>&1 | tail -n 40`. Grep logs for `error|fail` rather than reading them.
- Prefer `git diff --stat` then a targeted `git diff -- <file>`.
- Never print whole JSON payloads, DataFrames or large arrays; print shapes, heads and summary statistics.

**Edit, don't rewrite**
- Make targeted edits. Do not regenerate whole files to change a few lines.
- Do not reformat files you did not otherwise change (run formatters on changed files only).

**Plan small, act, verify**
- For tasks touching more than 3 files: write a 3–6 line plan first, then execute.
- Run independent reads/commands together in one step rather than one at a time.
- Test narrowly while iterating (`pytest path/to/test_file.py -k name`, `pytest --lf`); run the full relevant suite once before committing.
- If the same approach fails 3 times, stop, summarise what you tried and what you observed, and ask.
- One task per session. Start a new session for an unrelated task instead of carrying old context.
- Use the cheapest capable model/effort for mechanical work (renames, formatting, boilerplate); reserve larger models for maths, architecture and debugging.
- Do not spawn sub-agents unless asked; each one re-reads the repository.

**Report briefly**
- Final message: what changed (files), test results, anything left undone or uncertain. Do not paste full files or full diffs into chat.

## 4. Repository map

```text
packages/risk_core/     pure numerical library (no DB, network, LLM, or I/O)
packages/dag/           content-addressed computation DAG + receipts
packages/lookthrough/   ETF look-through, entity resolution, overlap
packages/ai/            prompts, schemas, lexicons, validators, renderer
packages/data_adapters/ provider adapters + licence checks
services/api/           FastAPI app (one module per bounded context)
services/worker/        background jobs (Procrastinate)
apps/web/               Next.js web app / PWA
cli/prl/                verify / replay / seed CLI
tests/                  unit, property, metamorphic, integration, e2e, security
docs/spec/              product spec (read by section only); docs/adr/ decisions
```

## 5. Commands

```bash
uv sync                                   # Python deps
uv run pytest -q -x                       # Python tests (add a path to narrow)
uv run ruff check --fix <files> && uv run ruff format <files>
uv run pyright                            # type check
pnpm install && pnpm -C apps/web lint && pnpm -C apps/web test
uv run alembic -c services/api/alembic.ini upgrade head
```
If a command here is wrong or missing, say so in your final message rather than guessing silently.

## 6. Coding rules

**General**
- Python 3.13, full type hints, `ruff` clean, `pyright` clean. TypeScript `strict`, no `any` without a comment explaining why.
- Small pure functions. No global state. No `except: pass` or `except Exception: return 0`; raise typed errors or return typed warnings.
- Add a dependency only when the standard library or an existing dependency can't do it. State the reason in the commit body.
- Comments explain *why*, not *what*. No commented-out code. No TODOs without an issue ID.

**Financial correctness (see spec §6–§7)**
- Money and quantities: `Decimal` / `NUMERIC`, never float. Convert to float64 arrays only inside analytics.
- Ratios as decimals (`0.05` = 5%); bp only in UI. Every money value carries an ISO currency.
- Instruments are identified by ISIN (+ MIC for listings), never by ticker alone.
- Missing data stays missing: never fill with zero, never interpolate returns. Report coverage.
- Quantile/ES convention is fixed (spec §7.1). Do not change it without an ADR.
- Every new metric ships with a hand-checked fixture and a property test.

**Architecture**
- `risk_core` stays pure: no imports of DB, HTTP, filesystem, or AI packages. CI enforces this.
- All results go through the DAG and produce a receipt. Do not compute numbers outside it.
- AI code never produces numbers; it emits references bound to receipt fields (spec §14.3).
- API changes: update the OpenAPI schema and regenerate the client in the same PR.
- DB changes: one Alembic migration per PR, expand/contract style, never edit an applied migration.

**Security and data**
- Never commit secrets, `.env`, real portfolio files, provider data, or signing keys. Use `.env.example`.
- No real user data in tests, fixtures, logs or screenshots; use `data/synthetic/`.
- No new external data source without a `data_licences` entry and an ADR.
- Do not log holdings, values, emails or tokens.
- Tests run offline. Mock network calls at the adapter boundary.

## 7. Definition of done

- [ ] Tests added/updated and passing; fixtures for any new maths.
- [ ] Lint and type checks pass on changed files.
- [ ] No unrelated changes in the diff.
- [ ] Docs/ADR updated if behaviour, API or conventions changed.
- [ ] Commit messages follow §1; no AI/agent references anywhere.
- [ ] Final report lists files changed, tests run and open questions.

## 8. When unsure

Ask one specific question rather than guessing, especially about money, tax, licensing, security or anything irreversible.
