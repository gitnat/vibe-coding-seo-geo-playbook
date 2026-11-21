# The SEO and GEO checklist for AI-built websites

Five steps. Steps 1 to 4 before launch, step 5 after. Every tool mentioned is free.

## 1. Plan before you build

Why: AI builds what you describe. Skip this and you can end up with a beautiful site that answers questions nobody is asking.

- Find what people search for (Google suggestions, "People also ask", Keyword Planner, Google Trends)
- Check what competitors cover
- Collect real customer questions (they become your FAQ and your AI answers)
- One topic per page
- Plan site structure and URLs (short, lowercase, hyphens, within three clicks of home)
- Give the AI your SEO rules before it builds (see the `seo-geo-brief` skill)

## 2. Get every page right

Why: each page is a separate entry in Google and in AI answers. Without its own title, description and heading they cannot tell pages apart.

- Its own title (under about 60 characters, topic first, brand last)
- A short description (140 to 160 characters, written for a person)
- One main heading (H1), then H2 and H3 in order
- Main address set (canonical, full https URL on the real domain)
- Page language set (`lang` on the html tag)
- Image descriptions (alt text), empty only for decoration
- Links to related pages, with text that says where they go
- Social preview image (Open Graph title, description, image, URL)

## 3. Fix the technical basics

Why: if crawlers cannot reach or read your pages, nothing else matters.

- Text in the code, not only JavaScript (most AI crawlers do not run JavaScript)
- https, one version of the domain (www or not, redirect the other)
- A sitemap (`/sitemap.xml`)
- A robots.txt file that links the sitemap and blocks nothing important
- Small, fast images with width and height set
- Looks good on a phone (viewport, no sideways scroll, easy taps)
- Old URLs redirected (301) when pages move
- No noindex on live pages (test and preview versions should be hidden instead)

## 4. Get found by AI (GEO)

Why: AI assistants answer questions by reading and quoting pages they can read, understand and trust.

- Let AI search bots in: OAI-SearchBot, ChatGPT-User, Claude-SearchBot, PerplexityBot. Blocking training bots like GPTBot or ClaudeBot is a separate business choice.
- Answer the question first, then explain
- Clear facts AI can quote (names, numbers, dates)
- Structured data (JSON-LD): Person or Organization, Article, FAQPage, Product, BreadcrumbList. Only mark up what is visible.
- Same name and bio everywhere, linked with `sameAs`
- Show author and date
- Earn mentions on trusted sites (industry sites, directories, press, communities)
- llms.txt (optional; a proposed convention, not a standard)

## 5. Launch, measure, improve

Why: launch is when Google, Bing and AI assistants start learning about your site.

- Set up Google Search Console
- Set up Bing Webmaster Tools (Bing's index feeds several AI assistants)
- Submit your sitemap to both
- Claim your ChatGPT business profile (ChatGPT Business Hub) and, for local businesses, your Google Business Profile
- Check key pages are indexed (URL Inspection)
- Track visits and searches
- Earn links from other sites
- Update content regularly and show the updated date

Full guide and PDF: https://natalliajarl.com/ai-playbooks/vibe-coding-seo/
