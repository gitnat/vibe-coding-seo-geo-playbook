#!/usr/bin/env python3
"""SEO and GEO pre-launch audit for AI-built websites.

Checks a local site folder (built HTML) or a live URL and prints a Markdown report:
a score per step and the issues sorted by impact, in plain language.

Usage:
  python3 audit.py ./dist --base https://example.com
  python3 audit.py https://example.com --max-pages 50
  python3 audit.py ./site --json

Python 3.8+, standard library only. Part of the vibe coding SEO and GEO playbook:
https://natalliajarl.com/ai-playbooks/vibe-coding-seo/
"""
import argparse, json, os, re, sys, urllib.error, urllib.parse, urllib.request
from collections import deque
from html.parser import HTMLParser
from xml.etree import ElementTree

AI_SEARCH_BOTS = ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "PerplexityBot"]
SKIP_DIRS = {"node_modules", ".git", ".next", ".nuxt", ".svelte-kit", ".cache", ".vercel", ".netlify", "__pycache__", "coverage", ".astro"}
UA = "Mozilla/5.0 (compatible; vibe-coding-seo-geo-audit/1.0; +https://natalliajarl.com/ai-playbooks/vibe-coding-seo/)"
STEPS = {1: "Plan before you build", 2: "Get every page right", 3: "Fix the technical basics", 4: "Get found by AI (GEO)", 5: "Launch, measure, improve"}


# ---------- parsing ----------
class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.in_title = "", False
        self.lang = None
        self.meta = {}
        self.links = []          # (rel, href)
        self.h1 = 0
        self.imgs = []           # dict attrs
        self.ld = []             # raw json-ld strings
        self.anchors = []
        self.text = []
        self._skip = 0
        self._ld = None
        self.heads = []          # H2/H3 text
        self._head = None
        self.glued = []          # "word|Word" pairs that touch across tags
        self._prev, self._ws, self._crossed = None, True, False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        self._crossed = True
        if tag == "br":
            self._ws = True
        if tag in ("h2", "h3") and not self._skip:
            self._head = ""
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append((a.get("rel", "").lower(), a.get("href", "")))
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a" and a.get("href"):
            self.anchors.append(a["href"])
        elif tag == "script":
            if "ld+json" in a.get("type", "").lower():
                self._ld = []
            else:
                self._skip += 1
        elif tag in ("style", "noscript", "template", "svg"):
            self._skip += 1

    def handle_endtag(self, tag):
        self._crossed = True
        if tag in ("h2", "h3") and self._head is not None:
            self.heads.append(re.sub(r"\s+", " ", self._head).strip()); self._head = None
        if tag == "title":
            self.in_title = False
        elif tag == "script":
            if self._ld is not None:
                self.ld.append("".join(self._ld)); self._ld = None
            elif self._skip:
                self._skip -= 1
        elif tag in ("style", "noscript", "template", "svg") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data); return
        if self.in_title:
            self.title += data; return
        if not self._skip:
            self.text.append(data)
            if self._head is not None:
                self._head += data
            if not data.strip():
                self._ws = True
                return
            if (self._crossed and self._prev and not self._ws and not data[0].isspace()
                    and self._prev == self._prev.rstrip()
                    and re.search(r"[\w)\]?!.:%]$", self._prev) and re.match(r"[\w(\"“']", data)):
                self.glued.append(self._prev.strip()[-20:] + "|" + data.strip()[:20])
            self._prev, self._ws, self._crossed = data, data[-1].isspace(), False

    def words(self):
        return len(re.findall(r"\w{2,}", " ".join(self.text)))


GENERIC_HEADINGS = {"about", "about us", "about me", "services", "features", "benefits", "overview", "introduction", "intro",
    "how it works", "all you need", "what you need", "see it in action", "get in touch", "contact", "contact us", "faq", "faqs",
    "questions", "questions people ask", "frequently asked questions", "pricing", "resources", "learn more", "read more", "more",
    "next steps", "summary", "conclusion", "welcome", "why", "why us", "our story", "my story", "the checklist", "prompts",
    "before launch", "after launch", "the problem", "the solution", "testimonials", "blog", "news"}


def is_generic(h):
    t = re.sub(r"^[\d\s.:)#-]+", "", h).strip(" ?!.:").lower()
    return t in GENERIC_HEADINGS


def ld_types(raw_list):
    """Return (types, valid, has_sameas, article_ok_or_None)."""
    types, valid, sameas, article = set(), True, False, None
    def walk(o):
        nonlocal sameas, article
        if isinstance(o, list):
            for x in o: walk(x)
        elif isinstance(o, dict):
            t = o.get("@type")
            for x in (t if isinstance(t, list) else [t] if t else []):
                types.add(str(x))
                if str(x) in ("Article", "BlogPosting", "NewsArticle", "TechArticle"):
                    ok = bool(o.get("author")) and bool(o.get("datePublished") or o.get("dateModified"))
                    article = ok if article is None else (article and ok)
            if o.get("sameAs"):
                sameas = True
            for v in o.values(): walk(v)
    for raw in raw_list:
        try:
            walk(json.loads(raw))
        except Exception:
            valid = False
    return types, valid, sameas, article


# ---------- fetching ----------
def _ssl_context():
    """Python on macOS often ships without root certificates. Fall back to certifi or a system bundle."""
    import ssl
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats().get("x509_ca", 0):
        return ctx
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    for path in ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt", "/usr/local/etc/openssl/cert.pem", "/opt/homebrew/etc/openssl@3/cert.pem"):
        if os.path.isfile(path):
            return ssl.create_default_context(cafile=path)
    return ctx

SSL_CTX = None
LAST_ERROR = ""

def fetch(url, timeout=15):
    global SSL_CTX, LAST_ERROR
    if SSL_CTX is None:
        SSL_CTX = _ssl_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
            body = r.read(3_000_000)
            cs = r.headers.get_content_charset() or "utf-8"
            return r.status, body.decode(cs, "replace"), r.geturl(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, "", url, ""
    except Exception as e:
        LAST_ERROR = str(getattr(e, "reason", e))
        return None, "", url, ""


def norm(u):
    """One form per page: no fragment, path '/' when empty, no index.html, lowercase host."""
    pr = urllib.parse.urlparse(u.split("#")[0])
    path = re.sub(r"(^|/)index\.html?$", r"\1", pr.path or "/") or "/"
    return urllib.parse.urlunparse((pr.scheme, pr.netloc.lower(), path, "", pr.query, ""))


def collect_folder(root, base, max_pages):
    files = []
    for d, dirs, fs in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("."))
        for f in sorted(fs):
            if f.lower().endswith((".html", ".htm")):
                files.append(os.path.join(d, f))
    files.sort(key=lambda p: (p.count(os.sep), p))
    pages = []
    for p in files:
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        if rel.lower() in ("404.html", "404/index.html"):
            continue
        path = "/" + re.sub(r"(^|/)index\.html?$", r"\1", rel)
        with open(p, encoding="utf-8", errors="replace") as fh:
            pages.append({"path": path, "url": (base.rstrip("/") + path) if base else path, "html": fh.read()})
        if len(pages) >= max_pages:
            break
    def read(name):
        fp = os.path.join(root, name)
        return open(fp, encoding="utf-8", errors="replace").read() if os.path.isfile(fp) else None
    site = {"robots": read("robots.txt"), "sitemap": read("sitemap.xml") or read("sitemap_index.xml"),
            "llms": read("llms.txt"), "has_404": os.path.isfile(os.path.join(root, "404.html")) or os.path.isfile(os.path.join(root, "404", "index.html")),
            "https": base.startswith("https://") if base else None,
            "total_html": len([f for f in files if not re.search(r"(^|/)404(\.html?|/index\.html?)$", os.path.relpath(f, root).replace(os.sep, "/"))])}
    return pages, site


def collect_url(start, max_pages):
    start = start if re.match(r"https?://", start) else "https://" + start
    status, body, final, _ = fetch(start)
    if status is None:
        hint = ""
        if "CERTIFICATE" in LAST_ERROR.upper():
            hint = ("\nPython could not verify the site's SSL certificate. On macOS, run 'Install Certificates.command' "
                    "in your Python folder, or 'pip install certifi', then try again.")
        sys.exit(f"Could not reach {start} ({LAST_ERROR or 'no response'}).{hint}")
    host = urllib.parse.urlparse(final).netloc
    origin = f"{urllib.parse.urlparse(final).scheme}://{host}"
    rs, robots, _, _ = fetch(origin + "/robots.txt")
    robots = robots if rs == 200 else None
    sm_urls = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots or "") or [origin + "/sitemap.xml"]
    sitemap_txt, queue = None, deque([final])
    ss, txt, _, _ = fetch(sm_urls[0])
    if ss == 200 and "<" in txt:
        sitemap_txt = txt
        for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", txt)[: max_pages * 2]:
            if urllib.parse.urlparse(loc).netloc == host and not loc.endswith(".xml"):
                queue.append(loc)
    ls, llms, _, _ = fetch(origin + "/llms.txt")
    nf, _, _, _ = fetch(origin + "/this-page-should-not-exist-404-check")
    pages, seen = [], set()
    while queue and len(pages) < max_pages:
        u = norm(queue.popleft())
        if u in seen:
            continue
        seen.add(u)
        s, b, fu, ct = (status, body, final, "text/html") if u == norm(final) and not pages else fetch(u)
        if s != 200 or ("html" not in ct.lower() and ct):
            continue
        fu = norm(fu)
        if fu != u:
            if fu in seen and any(p["url"] == fu for p in pages):
                continue  # a redirect to a page we already have
            seen.add(fu)
        path = urllib.parse.urlparse(fu).path or "/"
        pages.append({"path": path, "url": fu, "html": b})
        if not sitemap_txt:
            pp = PageParser(); pp.feed(b)
            for h in pp.anchors:
                nu = urllib.parse.urljoin(fu, h).split("#")[0]
                if urllib.parse.urlparse(nu).netloc == host and not re.search(r"\.(pdf|jpe?g|png|gif|webp|svg|zip|xml|txt)$", nu, re.I):
                    queue.append(nu)
    site = {"robots": robots, "sitemap": sitemap_txt, "llms": llms if ls == 200 and llms.strip() else None,
            "has_404": nf == 404, "https": final.startswith("https://"), "total_html": None}
    return pages, site, origin


# ---------- checks ----------
def robots_blocks(robots, agent):
    """True if robots.txt disallows '/' for this agent (exact group, else '*')."""
    groups, cur, last_was_ua = {}, [], False
    for line in (robots or "").splitlines():
        line = line.split("#")[0].strip()
        if ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        k = k.lower()
        if k == "user-agent":
            if not last_was_ua:
                cur = []
            cur.append(v.lower()); groups.setdefault(v.lower(), [])
            last_was_ua = True
        else:
            last_was_ua = False
            for ua in cur:
                groups[ua].append((k, v))
    rules = groups.get(agent.lower(), groups.get("*", []))
    allow_root = any(k == "allow" and v in ("/", "/*") for k, v in rules)
    return any(k == "disallow" and v in ("/", "/*") for k, v in rules) and not allow_root


def audit(pages, site, base):
    issues = []   # dict(step, sev, key, title, why, fix, pages)
    checks = {s: [] for s in STEPS}  # step -> list of (weight, pass_fraction)

    def add(step, sev, key, title, why, fix, bad):
        if bad:
            issues.append({"step": step, "sev": sev, "key": key, "title": title, "why": why, "fix": fix, "pages": bad})

    def page_check(step, w, sev, key, test, title, why, fix):
        bad = [p["path"] for p in pages if not test(p)]
        checks[step].append((w, 1 - len(bad) / max(1, len(pages))))
        add(step, sev, key, title.format(n=len(bad)), why, fix, bad)

    for p in pages:
        pp = PageParser(); pp.feed(p["html"]); p["pp"] = pp
        p["types"], p["ld_valid"], p["sameas"], p["article_ok"] = ld_types(pp.ld)
        p["canon"] = next((h for r, h in pp.links if "canonical" in r.split()), "")

    # Pages set to noindex are meant to be hidden (demos, previews): note them, check them against the sitemap,
    # and leave them out of the page checks so they do not drag the score down.
    hidden = [p for p in pages if "noindex" in p["pp"].meta.get("robots", "").lower()]
    sm_locs = set(urllib.parse.urlparse(u).path or "/" for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", site["sitemap"] or ""))
    in_sm = [p["path"] for p in hidden if p["path"] in sm_locs]
    if in_sm:
        checks[3].append((3, 0.0))
    add(3, 3, "noindex_sitemap", f"{len(in_sm)} noindex page(s) listed in the sitemap", "The sitemap says 'find this', the page says 'hide this'. If the page should be found, noindex is hiding it.",
        "Remove noindex if the page should be found, or remove it from the sitemap if not.", in_sm)
    notes = [p["path"] for p in hidden if p["path"] not in sm_locs]
    pages = [p for p in pages if p not in hidden]
    if not pages:
        return {}, 0, issues, notes

    titles = {}
    descs = {}
    for p in pages:
        t = p["pp"].title.strip(); d = p["pp"].meta.get("description", "").strip()
        if t: titles.setdefault(t, []).append(p["path"])
        if d: descs.setdefault(d, []).append(p["path"])

    # Step 1
    page_check(1, 1, 1, "urls", lambda p: not re.search(r"[A-Z_ %]|\.php|\?", p["path"]),
               "{n} page(s) with messy URLs", "Short, lowercase URLs with hyphens are easier to read, share and rank.",
               "Use lowercase words with hyphens, no underscores, spaces or parameters.")

    # Step 2
    page_check(2, 3, 3, "title", lambda p: p["pp"].title.strip(), "{n} page(s) without a title",
               "The title is the clickable headline in Google and the first thing AI reads.", "Give every page its own title, topic first, brand last.")
    dup_t = [pg for v in titles.values() if len(v) > 1 for pg in v]
    checks[2].append((2, 1 - len(dup_t) / max(1, len(pages))))
    add(2, 2, "title_dup", f"{len(dup_t)} page(s) share a title with another page", "Google cannot tell the pages apart, and they compete with each other.",
        "Write a unique title for each page.", dup_t)
    page_check(2, 1, 1, "title_len", lambda p: len(p["pp"].title.strip()) <= 65, "{n} title(s) longer than about 60 characters",
               "Long titles get cut off in search results.", "Keep titles under about 60 characters.")
    page_check(2, 3, 2, "desc", lambda p: p["pp"].meta.get("description", "").strip(), "{n} page(s) without a meta description",
               "Without one, Google picks random text for the snippet under your title.", "Add a 140 to 160 character description written for a person.")
    dup_d = [pg for v in descs.values() if len(v) > 1 for pg in v]
    checks[2].append((1, 1 - len(dup_d) / max(1, len(pages))))
    add(2, 1, "desc_dup", f"{len(dup_d)} page(s) share a description", "Copied descriptions make pages look the same in search.", "Write a unique description per page.", dup_d)
    page_check(2, 2, 2, "h1", lambda p: p["pp"].h1 == 1, "{n} page(s) without exactly one H1",
               "The H1 tells search engines and AI what the page is about. None, or several, makes it unclear.", "Use one H1 per page, then H2 and H3 in order.")
    page_check(2, 2, 2, "canonical", lambda p: p["canon"], "{n} page(s) without a canonical",
               "The canonical tells Google which address is the real one, so copies and previews do not compete.", "Add a canonical with the full https URL on your real domain.")
    if base:
        host = urllib.parse.urlparse(base).netloc
        page_check(2, 1, 2, "canon_host", lambda p: not p["canon"] or urllib.parse.urlparse(p["canon"]).netloc == host,
                   "{n} canonical(s) point to another domain", "A canonical to a preview or another domain tells Google to index that one instead.",
                   f"Point canonicals to {base}.")
    page_check(2, 1, 1, "lang", lambda p: p["pp"].lang, "{n} page(s) without a lang attribute",
               "The language tag helps search engines and screen readers.", 'Add lang to the html tag, for example <html lang="en">.')
    page_check(2, 2, 2, "alt", lambda p: all("alt" in i for i in p["pp"].imgs), "{n} page(s) with images missing alt text",
               "Alt text describes images for search, AI and people using screen readers.", "Describe each meaningful image. Use alt=\"\" only for decoration.")
    page_check(2, 1, 1, "og", lambda p: p["pp"].meta.get("og:title") and p["pp"].meta.get("og:image"), "{n} page(s) without a social preview",
               "Without Open Graph tags, shared links look plain or broken.", "Add og:title, og:description, og:image and og:url.")
    page_check(2, 1, 1, "headings", lambda p: not [h for h in p["pp"].heads if is_generic(h)],
               "{n} page(s) with generic headings", "Headings like 'How it works' or 'FAQ' say nothing on their own, so search engines and AI answers cannot tell what the section covers.",
               "Name the topic in each H2 and H3 with the words people search for, for example 'How the grocery dashboard works'.")
    page_check(2, 1, 2, "glued", lambda p: not p["pp"].glued, "{n} page(s) where words run together in the text",
               "Crawlers, AI tools and screen readers read the text without CSS, so <b>Calm</b>Soft becomes 'CalmSoft' and numbers glue to titles ('01Why').",
               "Put a space or line break between a label and the text after it, and between links, list items and spans. Keep section numbers out of heading text.")

    # Step 3
    page_check(3, 3, 3, "js_only", lambda p: p["pp"].words() >= 80, "{n} page(s) with little or no text in the HTML",
               "If the text only appears after JavaScript runs, most AI crawlers see an empty page and Google may see less.",
               "Render pages as static or server-side HTML so the text is in the code.")
    page_check(3, 2, 2, "viewport", lambda p: p["pp"].meta.get("viewport"), "{n} page(s) without a mobile viewport",
               "Without it, the page shows zoomed out on phones, where most people search.", 'Add <meta name="viewport" content="width=device-width, initial-scale=1">.')
    page_check(3, 1, 1, "img_size", lambda p: all(i.get("width") and i.get("height") for i in p["pp"].imgs), "{n} page(s) with images missing width and height",
               "Images without sizes make the layout jump while loading, which hurts Core Web Vitals.", "Set width and height on every image.")
    r = site["robots"]
    checks[3].append((2, 1.0 if r is not None else 0.0))
    add(3, 2, "robots", "No robots.txt", "Crawlers look for it first. It should link your sitemap and block nothing important.",
        "Add /robots.txt that allows crawling and links your sitemap.", ["(site)"] if r is None else [])
    sm = site["sitemap"]
    checks[3].append((2, 1.0 if sm else 0.0))
    add(3, 2, "sitemap", "No sitemap.xml", "The sitemap is the list of pages you want found.", "Add /sitemap.xml with every indexable page.", ["(site)"] if not sm else [])
    if r is not None:
        linked = bool(re.search(r"(?im)^\s*sitemap:", r))
        checks[3].append((1, 1.0 if linked else 0.0))
        add(3, 1, "robots_sitemap", "robots.txt does not link the sitemap", "Crawlers find your page list faster when robots.txt points to it.",
            "Add a line: Sitemap: https://yourdomain/sitemap.xml", [] if linked else ["(site)"])
        if robots_blocks(r, "*"):
            checks[3].append((3, 0.0))
            add(3, 3, "robots_all", "robots.txt blocks all crawlers", "Nothing on the site can be crawled.", "Remove 'Disallow: /' for User-agent: *.", ["(site)"])
    if sm:
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm)
        try:
            ElementTree.fromstring(sm.encode("utf-8")); ok = True
        except Exception:
            ok = False
        checks[3].append((1, 1.0 if ok and locs else 0.0))
        add(3, 1, "sitemap_bad", "sitemap.xml is empty or not valid XML", "Search engines cannot read a broken sitemap.", "Regenerate sitemap.xml with full https URLs.", [] if ok and locs else ["(site)"])
    checks[3].append((1, 1.0 if site["has_404"] else 0.0))
    add(3, 1, "404", "No real 404 page", "Missing pages should return status 404, not a blank page or the home page.", "Add a 404 page that returns status 404.", [] if site["has_404"] else ["(site)"])
    if site["https"] is not None:
        checks[3].append((1, 1.0 if site["https"] else 0.0))
        add(3, 2, "https", "Site is not on https", "Browsers warn visitors and search engines prefer secure sites.", "Serve the site over https and redirect http.", [] if site["https"] else ["(site)"])

    # Step 4
    if r is not None:
        blocked = [b for b in AI_SEARCH_BOTS if robots_blocks(r, b)]
        checks[4].append((3, 1 - len(blocked) / len(AI_SEARCH_BOTS)))
        add(4, 3, "ai_bots", f"robots.txt blocks AI search bots: {', '.join(blocked)}", "These bots fetch pages for answers in ChatGPT, Claude and Perplexity. Blocked means not cited.",
            "Allow AI search bots in robots.txt. Blocking training bots like GPTBot is a separate choice.", ["(site)"] if blocked else [])
    page_check(4, 2, 2, "schema", lambda p: p["types"], "{n} page(s) without structured data",
               "Structured data (JSON-LD) tells search engines and AI exactly who you are and what each page is.",
               "Add JSON-LD: Person or Organization, plus Article, FAQPage or Product where it fits.")
    bad_ld = [p["path"] for p in pages if p["pp"].ld and not p["ld_valid"]]
    checks[4].append((1, 1 - len(bad_ld) / max(1, len(pages))))
    add(4, 2, "schema_bad", f"{len(bad_ld)} page(s) with broken JSON-LD", "Broken structured data is ignored.", "Fix the JSON syntax and test in the Rich Results Test.", bad_ld)
    has_sameas = any(p["sameas"] for p in pages)
    checks[4].append((1, 1.0 if has_sameas else 0.0))
    add(4, 1, "sameas", "No sameAs links in structured data", "sameAs connects your site to your profiles, so AI knows it is the same person or company.",
        "Add sameAs with your LinkedIn and other profiles to your Person or Organization JSON-LD.", [] if has_sameas else ["(site)"])
    art_bad = [p["path"] for p in pages if p["article_ok"] is False]
    if any(p["article_ok"] is not None for p in pages):
        checks[4].append((1, 1 - len(art_bad) / max(1, len(pages))))
        add(4, 1, "author_date", f"{len(art_bad)} article(s) without author or date in structured data", "AI tools prefer content with a clear source and a recent date.",
            "Add author and datePublished or dateModified to Article JSON-LD, and show them on the page.", art_bad)
    has_llms = bool(site["llms"])
    checks[4].append((1, 1.0 if has_llms else 0.0))
    add(4, 1, "llms", "No llms.txt (optional)", "A short summary of the site for AI tools. A proposed convention, not a standard, but quick to add.",
        "Add /llms.txt with a one-paragraph summary and links to your key pages.", [] if has_llms else ["(site)"])

    scores = {}
    for s, lst in checks.items():
        if lst:
            tw = sum(w for w, _ in lst)
            scores[s] = round(100 * sum(w * f for w, f in lst) / tw)
    weights = {1: 1, 2: 3, 3: 3, 4: 3}
    overall = round(sum(scores[s] * weights[s] for s in scores) / sum(weights[s] for s in scores)) if scores else 0
    issues.sort(key=lambda i: (-i["sev"], -len(i["pages"]), i["step"]))
    return scores, overall, issues, notes


# ---------- report ----------
def report_md(target, pages, site, scores, overall, issues, notes):
    sev = {3: "High", 2: "Medium", 1: "Low"}
    out = [f"# SEO and GEO audit: {target}", "", f"Pages checked: {len(pages)}"
           + (f" (of {site['total_html']} HTML files)" if site.get("total_html") and site["total_html"] > len(pages) else ""), "",
           f"## Overall score: {overall}/100", "", "| Step | Score |", "|---|---|"]
    for s, name in STEPS.items():
        out.append(f"| {s}. {name} | {str(scores[s]) + '/100' if s in scores else 'Manual check'} |")
    out += ["", "Step 5 (Search Console, Bing, ChatGPT and Google business profiles, links and mentions) happens outside the code, so it is a manual check.", ""]
    if not issues:
        out += ["## Issues", "", "No issues found by the automated check. Do the manual checks next."]
    else:
        out += ["## Issues, biggest impact first", "", "| Impact | Step | Issue | Why it matters | Fix | Pages |", "|---|---|---|---|---|---|"]
        for i in issues:
            pg = ", ".join(i["pages"][:5]) + (f" and {len(i['pages']) - 5} more" if len(i["pages"]) > 5 else "")
            out.append(f"| {sev[i['sev']]} | {i['step']} | {i['title']} | {i['why']} | {i['fix']} | {pg} |")
        out += ["", "## Fix these first", ""]
        for n, i in enumerate(issues[:3], 1):
            out.append(f"{n}. {i['fix']} ({i['title'].lower()})")
    if notes:
        out += ["", "## Hidden pages (noindex)", "", "These pages are set to noindex and are not in the sitemap, so they look intentionally hidden (demos, previews, thank-you pages). They were left out of the score. If any should be found, remove noindex: " + ", ".join(notes)]
    out += ["", "## Manual checks (code cannot see these)", "",
            "- Does each key page answer its main question in the first one or two sentences?",
            "- Are there clear, quotable facts (names, numbers, dates)?",
            "- Same name, title and description on the site, LinkedIn and directories?",
            "- Google Search Console and Bing Webmaster Tools set up, sitemap submitted?",
            "- ChatGPT business profile (and Google Business Profile if local) claimed?",
            "- Links and mentions from trusted sites?", "",
            "Checklist and guide: https://natalliajarl.com/ai-playbooks/vibe-coding-seo/"]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="SEO and GEO pre-launch audit for AI-built websites.")
    ap.add_argument("target", help="Site folder with built HTML, or a live URL")
    ap.add_argument("--base", default="", help="Production URL for a folder audit, e.g. https://example.com")
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    a = ap.parse_args()
    if os.path.isdir(a.target):
        pages, site = collect_folder(a.target, a.base, a.max_pages)
        base = a.base
    else:
        pages, site, base = collect_url(a.target, a.max_pages)
    if not pages:
        sys.exit("No HTML pages found. Point the audit at the built site folder (for example dist/ or build/) or a live URL.")
    scores, overall, issues, notes = audit(pages, site, base)
    if a.json:
        print(json.dumps({"target": a.target, "pages": len(pages), "overall": overall, "scores": scores, "issues": issues, "hidden_pages": notes}, indent=2))
    else:
        print(report_md(a.target, pages, site, scores, overall, issues, notes))


if __name__ == "__main__":
    main()
