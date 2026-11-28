# SEO and GEO rules file

Copy this into the project's CLAUDE.md, the Claude Project instructions or the start of the chat. Replace the placeholders.

```text
SEO and GEO rules for this website
Domain: https://[your-domain.com]
Owner: [your name], [your title]

Follow these rules on every page you create or change. If a rule conflicts with a design request, ask me before you break it.

RENDERING
- All main content must be in the HTML the server sends. No text that only appears after JavaScript runs.

EVERY PAGE
- One H1 that says what the page is about. Then H2 and H3 in order, no skipped levels.
- A unique title, under 60 characters, main topic first and the brand last.
- A unique meta description, 140 to 160 characters, written for a person, not for keywords.
- A canonical tag with the full https URL on the production domain.
- The lang attribute on the html tag, matching the page language.
- Open Graph title, description, image and URL.
- Short, lowercase URLs with hyphens.
- Descriptive link text, never "click here". Link related pages to each other.

HEADINGS AND TEXT
- Every H2 and H3 names its topic with the words people search for, and makes sense on its own. Not "How it works" but "How the grocery dashboard works". Not "Questions people ask" but "Questions about vibe coding SEO".
- No generic headings on their own: About, Services, Features, How it works, Get in touch, FAQ. Add what it is about.
- Section numbers and icons are decoration. Draw them with CSS, keep them out of the heading text.
- Words must never run together in the HTML text. Put a space or line break between a label and the text after it, and between links, list items, buttons and spans: <b>Calm</b> Soft colours, not <b>Calm</b>Soft colours. Crawlers, AI tools and screen readers read the text without your CSS.

IMAGES AND SPEED
- Descriptive alt text on every image that carries meaning. Empty alt only for decoration.
- Width and height on every image. Compress images and lazy-load the ones below the fold.
- Mobile first: no sideways scrolling, readable text, buttons easy to tap.

SITE FILES
- sitemap.xml with every page that should be indexed. Update it when pages change.
- robots.txt that allows search engines and AI search crawlers (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, PerplexityBot) and links the sitemap.
- llms.txt with a short summary of the site and links to the key pages.
- A real 404 page that returns status 404.
- Preview and test pages: noindex, or a canonical to the production URL. Never noindex on production.

STRUCTURED DATA
- JSON-LD on every page: Person or Organization, BreadcrumbList, plus Article, FAQPage or Product where it fits.
- Only mark up what is visible on the page.

GEO
- Start every page and every section with a direct answer in one or two sentences.
- Write facts plainly: who, what, where, numbers, dates. Make key lines easy to quote.
- Use the same name, title and description everywhere, and link my profiles with sameAs.
- Show the author and a last updated date on articles and guides.

BEFORE YOU SAY DONE
- List every page with its title, description, H1, H2s and canonical so I can check them.
- Read each page's text with the CSS turned off (for example document.body.textContent) and fix any words that run together.
- Check the layout at 375 px wide and on desktop.
- Never remove existing SEO tags, structured data or redirects without asking me.
```

Source: https://natalliajarl.com/ai-playbooks/vibe-coding-seo/
