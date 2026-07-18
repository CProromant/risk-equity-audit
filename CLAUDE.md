CLAUDE.md

Read PROTOCOL.md first — it is the binding spec (architecture, data sources, phases, acceptance criteria). Execute phase by phase; do not advance with acceptance criteria unmet. This file governs how the code reads. On style, this file wins.

Voice

Write like one careful researcher who codes daily, not like a code generator. The test for every line: would a senior data scientist, writing quickly but well, produce it? If a line exists to explain the obvious, impress, or hedge, delete it.

Comments


Comments explain why, never what. If the code needs a what-comment, rewrite the code instead.
No banner comments (# ===== Load data =====), no numbered-step comments, no comment restating the line below it.
No chat residue, ever: "Here we...", "Note that...", "As requested", # rest of the code, placeholder TODOs.
A file with zero comments is normal. Real TODOs are fine only when something is genuinely deferred: # TODO: two-part model (backlog, PROTOCOL §7). Never invent one.


Docstrings


Public API of riskaudit.audit: full NumPy-style docstrings with the exact math — PROTOCOL §4.4 requires it.
Everything else: one line or nothing. No Args/Returns scaffolding on trivial functions. Never open with "This function".


Structure


Simplest thing that works. Functions over classes; a class must earn its existence with state plus behavior. No abstract bases, factories, or config objects for two parameters.
Do not extract a helper before the third real use. Duplicating twice is cheaper than the wrong abstraction.
Scripts read top to bottom: constants, functions, if __name__ == "__main__":. No framework ceremony.
Let it crash. No try/except unless the except does something specific. Validate at data boundaries (ETL); trust internal calls.
No logging framework. A terse print at script level for progress is fine. No emoji, no exclamation marks.


Naming


Domain shorthand a colleague would use: wt, k6, df, topk, oof, capture. Short names in tight scopes (i, col, m).
Banned generator vocabulary: data, result, temp, process_, handle_, my_, _list/_dict suffixes, enhanced, comprehensive, robust, utils grab-bags.
Type hints on public signatures. Skip locals and obvious internals.


Pandas / analysis idiom


Moderate method chains (2–4 steps), then a named intermediate. Never a ten-step chain; never .copy() reflexively.
Vectorize. No iterrows unless unavoidable — and then one comment saying why.
Test fixtures use MEPS-plausible values (ages 18–85, K6 in 0–24, right-skewed costs), never foo/bar or tidy round numbers.


Tests


Plain pytest functions, no test classes. One behavior per test; hand-computed expected values in the audit tests. Names describe behavior: test_capture_weights_change_result, not test_1.


README and prose


Plain and factual, first person singular where natural ("I use the Panel 26 file because..."). No emoji, no "Features 🚀", no comprehensive/leverages/seamless/state-of-the-art. Badges: CI, license, DOI — nothing else.


Commits


Subject ≤ 60 chars, imperative, conventional prefix per PROTOCOL §6. Body only when the why is not obvious: one to three plain sentences. Never bullet-list what the diff already shows. One logical change per commit — mixed commits are the strongest generator tell.


Dependencies and imports


Only what is used; stdlib first. No dependency for what ten lines of stdlib can do. Remove dead imports before committing.


Hard limits — do not "humanize"


Never introduce deliberate typos, bugs, dead code, or artificial inconsistency to look human. Human-quality means fewer defects, not planted ones.
Never rewrite git history or fake timestamps or authorship.
Formatter-enforced consistency (ruff) is normal for humans too. Keep it.


Self-check before closing any file

Read it once asking: is there any line whose existence could only be explained with "the tool put it there"? If yes, delete or rewrite until every line has a reason the author can state out loud — in a code review or a thesis defense.