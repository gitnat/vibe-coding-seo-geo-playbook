---
name: seo-geo-brief
description: Use before building, rebuilding or redesigning a website with AI (vibe coding), so the site is set up for Google and AI search (SEO and GEO) from the first line of code. Plans keywords and site structure, then writes SEO and GEO rules into the project.
---

# SEO and GEO brief: set the rules before you build

AI builds what it is told. Asking it to "add some SEO" at the end gives vague results and means touching every page again. This skill sets the rules first, so every page you create follows them.

Part of the vibe coding SEO and GEO playbook by Natallia Jarl: https://natalliajarl.com/ai-playbooks/vibe-coding-seo/

## Step 1: ask four short questions

Ask the user, in one message, and wait for the answers:

1. What is the domain (or the planned domain)?
2. Whose site is it: name, and title or one-line description of the business?
3. Which languages will the site have?
4. Who is it for, and what are 5 to 10 questions those people ask?

If the user cannot answer one, use a clear placeholder and say so.

## Step 2: plan before building

Using the answers, propose a plan and show it as a table before building anything:

| Page | URL | Main search it should win | Question it answers first |
|---|---|---|---|

Rules for the plan:
- One topic per page, so pages do not compete.
- Short, lowercase URLs with hyphens. Every important page within three clicks of the home page.
- Base the "main search" on how people really phrase things. Suggest the user checks Google suggestions, "People also ask", Google Keyword Planner and Google Trends. Do not invent search volumes.
- Turn the user's customer questions into page openings and FAQ entries.

Wait for the user to confirm or change the plan.

## Step 3: write the rules into the project

Take the rules file in `references/rules-file.md`, fill in the domain, owner and languages, and save it where it will be read on every task:
- In Claude Code: add it to `CLAUDE.md` in the project root (create the file if needed, append if it exists, never overwrite other content).
- In a Claude Project: give the user the filled-in text to paste into the project instructions.
- Otherwise: keep it at the top of the conversation and follow it.

Add the confirmed page plan from Step 2 under a heading `## Site plan` in the same place.

## Step 4: build by the rules

From now on, every page you create or change follows the rules file. Before saying a page is done, list its title, meta description, H1 and canonical so the user can check them.

When the site is close to launch, suggest running the `seo-geo-audit` skill.

## Tone

Plain language. Explain a technical term the first time you use it, in brackets. No jargon walls.
