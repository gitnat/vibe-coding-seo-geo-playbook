---
name: seo-geo-audit
description: Use when a website built with AI (vibe coded) is close to launch or already live and the user wants to know if Google and AI assistants like ChatGPT and Gemini can find it. Runs a pre-launch SEO and GEO check on a local site folder or a live URL and gives a prioritized, plain-language fix list.
---

# SEO and GEO audit: check before you launch

A calm, practical check for websites built with AI. It finds what AI tools usually skip, explains it in plain words, sorts fixes by impact, and changes nothing until the user says yes.

Part of the vibe coding SEO and GEO playbook by Natallia Jarl: https://natalliajarl.com/ai-playbooks/vibe-coding-seo/

## Step 1: find what to check

- If the user is in a project folder, look for the built output (for example `dist/`, `build/`, `out/`, `public/` or the folder with `index.html`). If the site is a JavaScript app that only builds in the browser, build it or use its static export first, and tell the user that this matters (see the "JavaScript only" item in the checklist).
- If the site is live, use its URL.

## Step 2: run the automated check

Run the script that comes with this skill (Python 3, no extra packages):

```bash
python3 scripts/audit.py <site-folder-or-url>
```

Use the path to `scripts/audit.py` inside this skill's folder. Add `--base https://example.com` for a folder, so canonicals and the sitemap can be checked against the real domain. Add `--max-pages 50` to check more pages (default 30).

The script checks every page for title, description, one H1, canonical, language, alt text, image sizes, social preview, noindex, structured data and whether the text is in the HTML. It checks the site for robots.txt (including AI search bots), sitemap.xml, llms.txt and a real 404 page. It prints a score per step and a list of issues sorted by impact.

If the script cannot run (no Python, no network), do the same checks by reading the files yourself, and say so.

## Step 3: check what code cannot

Read the home page and the 2 or 3 most important pages and judge, using `references/checklist.md`:
- Does each page answer its main question in the first one or two sentences?
- Are there clear, quotable facts (names, numbers, dates) that make sense on their own?
- Is the same name, title and description used everywhere, with `sameAs` links to profiles?
- Is there an author and an updated date on articles and guides?
- Does each page have one clear topic?

Then remind the user of the off-site steps no audit of the code can see: Google Search Console, Bing Webmaster Tools, claiming their ChatGPT and Google business profiles, and earning links and mentions on trusted sites.

## Step 4: report

Give the user:
1. The score per step (1 Plan, 2 Every page, 3 Technical, 4 GEO, 5 Launch) in one short table.
2. A table of issues: page, what is wrong, why it matters (one plain sentence), fix. Biggest impact first. Group repeated issues ("12 pages have no description") instead of listing each page.
3. The three fixes to do first.

Do not change any file yet. Ask which fixes to make.

## Step 5: fix and re-check

Make only the fixes the user approves. Never remove existing SEO tags, structured data or redirects without asking. After fixing, run the script again and show the before and after score.

## Tone

Plain language, no jargon walls, no alarmism. A score is a guide, not a verdict. If the site is in good shape, say so.
