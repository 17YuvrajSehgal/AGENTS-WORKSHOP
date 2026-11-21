# How to write a paper note in this folder

You are writing reading notes for a researcher (M.Sc. student; English is not his first language).
He will cite these papers in a workshop paper and the notes are his source, so accuracy matters more than anything else.
The authors of some of these papers sit on the program committee. A wrong number or a wrong claim in a note can end up in the paper.

## What you get

- The PDF: `C:\workplace\JiraAndLogs\AGENTS-WORKSHOP\related-papers\<file>.pdf`
- Its text (from `pdftotext -layout`): `C:\workplace\JiraAndLogs\AGENTS-WORKSHOP\related-papers\_txt\<key>.txt`.
  Read the text file in full, in parts of about 600 lines with the Read tool (offset/limit). Do not skip the appendix, tables or threats section.
- Tables and figures can be garbled in the text. When a number matters and the text is unclear, look at the page:
  `MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -- pdftoppm -f <page> -l <page> -r 90 -png "/mnt/c/workplace/JiraAndLogs/AGENTS-WORKSHOP/related-papers/<file>.pdf" /mnt/c/workplace/JiraAndLogs/AGENTS-WORKSHOP/related-papers/_txt/<key>-p`
  then Read the PNG it writes (`_txt/<key>-p-<page>.png`), and delete the PNG afterwards.
  The Read tool's `pages` option for PDFs does not work on this machine. PDFs of 10 pages or fewer can be read directly with Read (no `pages`).

## Format

Follow the structure of this finished example exactly (same headings, same order, same level of detail):
`C:\workplace\JiraAndLogs\AGENTS-WORKSHOP\related-papers\notes\mytkowicz2009wrong.md`

Read it fully before you start. In the header use:
- **PDF:** `related-papers/<file>.pdf`
- **Cite key:** the key given to you (it is the key in `paper/refs.bib`; do not invent another).

After the example's last section, add one more section:

## Connection to "Below the Stopwatch"

Our paper: coding agents open pull requests that claim to make code faster, and usually give a reason (a mechanism: "cache the result", "read the file once", "remove the lock"). We take performance PRs from the AIDev dataset, extract the claimed mechanism, map it to the kernel or hardware signal that must move if the claim is true (fewer `read` syscalls, fewer page faults, less futex wait, fewer instructions), let a build agent that never sees the claim rebuild the code before and after the PR and write a workload, and measure both versions with untraced timing, perf hardware counters and LTTng kernel traces on dedicated CPU cores, with a base-against-base (A/A) control. We then say per PR: faster or not, did the claimed mechanism happen, hidden costs, output changed.

In this section write:
- **How it relates:** 2 to 4 bullets. What this paper does that we build on, what it does not do that we do, and any point where it weakens or contradicts our approach. Be honest about the last one.
- **Safe to cite for:** 3 to 6 statements we could make in our paper with this citation. Each one must be supported by the paper, with the section or page and, where possible, a short exact quote in quotation marks.
- **Do not cite for:** things that sound like this paper but that it does not actually show.

## Rules

- Read everything: abstract, introduction, method, results, every table and figure, threats, future work, appendix.
- Go section by section. For results and tables, say what the numbers mean, not only what they are.
- Flag method weaknesses and things the authors glossed over.
- Every number must come from the paper. Give the section, table or page for the important ones. If the text extraction is unclear and you could not confirm a number on the page image, write "(unclear in the PDF)" instead of guessing.
- Never fill a gap from memory or from what similar papers say. If the paper does not say something, write "the paper does not say".
- Simple, clear English. Short sentences. Explain each technical term the first time, as if teaching it.
- No long dashes. No phrases like "it is worth noting", "it is important to note".
- Point out anything that connects to performance tracing or kernel analysis.

## When you finish

Write each note to `C:\workplace\JiraAndLogs\AGENTS-WORKSHOP\related-papers\notes\<key>.md` with the Write tool.
Do not edit any other file. Do not touch other notes.
Your final message: one line per paper with the note path, the number of lines, and anything you could not verify.
