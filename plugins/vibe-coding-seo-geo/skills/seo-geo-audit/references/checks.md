# Automated-style checks and scoring

Do these checks by reading the files (local folder) or fetching the pages (live URL). Check up to 30 pages: start from the home page, then the sitemap, then internal links. Leave out pages set to noindex that are not in the sitemap (demos, previews, thank-you pages) and list them separately as "hidden pages".

Each check has a weight (W) and an impact (High, Medium, Low). For page checks, the pass rate is the share of pages that pass. For site checks, it is 1 or 0.

## Step 1: Plan before you build

| Check | W | Impact | Pass when |
|---|---|---|---|
| Clean URLs | 1 | Low | Path is lowercase, uses hyphens, no underscores, spaces, `.php` or `?` parameters |

## Step 2: Get every page right

| Check | W | Impact | Pass when |
|---|---|---|---|
| Title | 3 | High | `<title>` is not empty |
| Unique title | 2 | Medium | No other page has the same title |
| Title length | 1 | Low | Title is about 60 characters or less (65 max) |
| Meta description | 3 | Medium | `<meta name="description">` is not empty |
| Unique description | 1 | Low | No other page has the same description |
| One H1 | 2 | Medium | Exactly one `<h1>` |
| Canonical | 2 | Medium | `<link rel="canonical">` with a full https URL |
| Canonical domain | 1 | Medium | Canonical points to the real domain, not a preview or other domain (only if the domain is known) |
| Language | 1 | Low | `<html lang="...">` is set |
| Alt text | 2 | Medium | Every `<img>` has an `alt` attribute (`alt=""` is fine for decoration) |
| Social preview | 1 | Low | `og:title` and `og:image` are set |
| Specific headings | 1 | Low | No H2 or H3 is only a generic phrase such as About, Services, Features, How it works, All you need, See it in action, Get in touch, Contact, FAQ, Questions people ask, Before launch (ignore a leading number). Headings should name their topic |
| No glued text | 1 | Medium | In the text without CSS (raw HTML text), no word ends right where the next text starts across a tag, for example `<b>Calm</b>Soft` read as "CalmSoft", `<a>Story</a><a>Work</a>` read as "StoryWork", or a section number glued to its title ("01Why") |

## Step 3: Fix the technical basics

| Check | W | Impact | Pass when |
|---|---|---|---|
| Text in the HTML | 3 | High | At least about 80 words of visible text in the raw HTML, before JavaScript runs |
| Mobile viewport | 2 | Medium | `<meta name="viewport">` is set |
| Image sizes | 1 | Low | Every `<img>` has `width` and `height` |
| robots.txt | 2 | Medium | `/robots.txt` exists |
| robots.txt links sitemap | 1 | Low | robots.txt has a `Sitemap:` line |
| Not blocking everything | 3 | High | robots.txt does not have `Disallow: /` for `User-agent: *` (only counts if it fails) |
| sitemap.xml | 2 | Medium | `/sitemap.xml` exists |
| Valid sitemap | 1 | Low | sitemap.xml is valid XML with at least one `<loc>` |
| Real 404 | 1 | Low | A made-up address returns status 404 (live), or a `404.html` exists (folder) |
| https | 1 | Medium | The live site loads on https (live only) |

## Step 4: Get found by AI (GEO)

| Check | W | Impact | Pass when |
|---|---|---|---|
| AI search bots allowed | 3 | High | robots.txt does not block OAI-SearchBot, ChatGPT-User, Claude-SearchBot, PerplexityBot. Score is the share allowed. Blocking training bots like GPTBot is a separate choice and does not count |
| Structured data | 2 | Medium | Page has JSON-LD with an `@type` |
| Valid JSON-LD | 1 | Medium | Every JSON-LD block parses |
| sameAs | 1 | Low | At least one Person or Organization on the site has `sameAs` links |
| Author and date | 1 | Low | Article or BlogPosting JSON-LD has `author` and `datePublished` or `dateModified` (only if the site has articles) |
| llms.txt | 1 | Low | `/llms.txt` exists (optional convention, quick to add) |

## Scoring

- Step score = sum of (W x pass rate) / sum of W, as a number out of 100.
- Overall = weighted average of the step scores: Step 1 x1, Step 2 x3, Step 3 x3, Step 4 x3.
- Step 5 (Search Console, Bing, business profiles, links and mentions) is outside the code, so it is a manual check and not scored.
- Sort issues by impact, then by how many pages they affect. Group repeated issues ("12 pages have no description").

Be honest about precision: if you could not fetch something (blocked, timeout), say which check was skipped and leave it out of the score instead of guessing.
