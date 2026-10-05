"""Build the generated parts of the public website from the library index and the article sources.

  bot/.venv/bin/python site-home/build/build_site.py

Writes, inside site-home/:
  library/index.html + library/docs.json   every public document, searchable, each open tracked
  articles/index.html + articles/<slug>/    FAQ articles from articles/src/*.json (Article + FAQPage structured data)
  privacy/index.html, terms/index.html      policies
  sitemap.xml                               for Google Search Console
The home page (index.html) is hand-written and only links to these.
"""
from __future__ import annotations

import datetime as dt
import glob
import html
import json
import os
import re
import sqlite3
import sys

import markdown

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SITE)
DB = os.path.join(ROOT, "bot", "index", "kb.sqlite")
CFG = json.load(open(os.path.join(SITE, "site.json")))
BASE, APP, NAME = CFG["base_url"], CFG["app_url"], CFG["name"]
TODAY = dt.date.today().isoformat()
E = html.escape

# public label for each library collection; collections not listed here are never published
CATEGORY = {
    "central_rules": "Central rules and orders", "official_updates": "Central rules and orders",
    "central_de": "Discipline and vigilance", "teachers": "KVS and NVS",
    "case_law_sc": "Supreme Court judgments", "case_law_hc_de": "Delhi High Court judgments",
    "case_law_hc_service": "Delhi High Court judgments", "case_law_hc_criminal": "Delhi High Court judgments",
    "dp_rules": "Delhi Police", "dp_standing_orders": "Delhi Police", "dp_welfare": "Delhi Police",
    "dp_legal_bulletins": "Delhi Police", "dp_rti_manuals": "Delhi Police", "danips": "Delhi Police",
    "criminal_acts": "Criminal law", "delhi_govt": "Delhi Government", "dda_land_law": "Delhi land and DDA", "dda_land_procedures": "Delhi land and DDA",
}
CATEGORY_ORDER = ["Central rules and orders", "Discipline and vigilance", "KVS and NVS", "Supreme Court judgments",
                  "Delhi Government", "Delhi High Court judgments", "Delhi Police", "Criminal law", "Delhi land and DDA"]


# ---------------------------------------------------------------- page shell
def page(title: str, description: str, path: str, body: str, active: str = "", head: str = "") -> str:
    canonical = BASE + path
    verify = (f'<meta name="google-site-verification" content="{E(CFG["google_site_verification"])}">'
              if CFG.get("google_site_verification") else "")
    nav = "".join(f'<a href="{BASE}{p}"{" aria-current=\"page\"" if active == k else ""}>{k}</a>'
                  for k, p in (("Latest", "latest/"), ("Articles", "articles/"), ("Library", "library/")))
    nav = nav.replace(f'{BASE}#how', f'{BASE}#how')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0b0b0c">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<link rel="canonical" href="{E(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:url" content="{E(canonical)}">
<meta property="og:image" content="{BASE}img/og.jpg">
{verify}
<link rel="icon" href="{BASE}icon.svg" type="image/svg+xml">
<link rel="preload" href="{BASE}fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{BASE}assets/site.css">
<script>window.SRA = {{ga: {json.dumps(CFG.get("ga_id", ""))}}};</script>
<script src="{BASE}assets/analytics.js" defer></script>
{head}
</head>
<body>
<a class="skip" href="#main">Skip to Content</a>
<header class="nav"><div class="wrap">
  <a class="brand" href="{BASE}"><img src="{BASE}icon.svg" alt="" width="26" height="26"><span translate="no">{E(NAME)}</span></a>
  <nav class="navlinks" aria-label="Sections">{nav}</nav>
  <a class="btn btn-primary btn-sm" href="{APP}" data-track="open_assistant" data-from="{E(path or 'home')}"><span>Open<span class="long"> the Assistant</span></span></a>
</div></header>
<main id="main">
{body}
</main>
<footer class="site"><div class="wrap">
  <span>{E(NAME)} is an independent project, not a government service. Answers explain the rules; they are not legal advice.</span>
  <nav aria-label="Site"><a href="{BASE}latest/">Latest</a><a href="{BASE}articles/">Articles</a><a href="{BASE}library/">Library</a><a href="{BASE}feedback/">Suggest</a><a href="{BASE}privacy/">Privacy</a><a href="{BASE}terms/">Terms</a></nav>
</div></footer>
</body>
</html>
"""


def write(rel: str, text: str) -> None:
    path = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def ld(obj) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


# ---------------------------------------------------------------- library
def norm_date(raw: str | None, doc_id: str, title: str) -> str:
    """Best-effort ISO date (YYYY-MM-DD or YYYY) for sorting."""
    for s in (raw or "", title):
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            return m.group(0)
        m = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b", s)
        if m:
            d, mo, y = m.groups()
            if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
                return f"{y}-{int(mo):02d}-{int(d):02d}"
    m = re.search(r"(?:^|[/_])((?:19|20)\d{2})[_-]", doc_id) or re.search(r"\b((?:19|20)\d{2})\b", raw or "")
    return m.group(1) if m else ""


def pretty_date(iso: str) -> str:
    if len(iso) == 10:
        try:
            return dt.date.fromisoformat(iso).strftime("%-d %b %Y")
        except ValueError:
            return iso
    return iso


def build_library() -> int:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = con.execute("""SELECT doc_id, collection, max(title), max(source_url), max(doc_date) FROM chunks
                          GROUP BY doc_id""").fetchall()
    docs, seen = [], set()
    for doc_id, coll, title, url, date in rows:
        cat = CATEGORY.get(coll)
        if not cat or not url or not url.startswith("http") or "UNOFFICIAL" in (title or "").upper():
            continue
        title = re.sub(r",? p\. \d+(-\d+)?$", "", (title or "").strip())
        key = (title.lower(), url)
        if key in seen:
            continue
        seen.add(key)
        iso = norm_date(date, doc_id, title)
        if iso == TODAY or "FAQ page" in title:   # a web page saved today, not an order dated today
            iso = ""
        docs.append({"t": title, "c": cat, "d": iso, "y": pretty_date(iso), "u": url})
    docs.sort(key=lambda d: (d["d"] or "0000"), reverse=True)
    write("library/docs.json", json.dumps(docs, ensure_ascii=False, separators=(",", ":")))
    counts = {c: sum(1 for d in docs if d["c"] == c) for c in CATEGORY_ORDER}
    chips = '<button class="chip" type="button" data-cat="" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" type="button" data-cat="{E(c)}" aria-pressed="false">{E(c)} <span class="muted">{n}</span></button>'
        for c, n in counts.items() if n)
    body = f"""<div class="wrap">
  <h1>Library of Official Documents</h1>
  <p class="lead">{len(docs):,} rules, orders, notifications, manuals and judgments the assistant answers from. Every link opens the official copy. Updated {pretty_date(TODAY)}.</p>
  <div class="toolbar">
    <label class="sr" for="q" hidden>Search documents</label>
    <input class="search" id="q" type="search" placeholder="Search by title, number or subject…" autocomplete="off" spellcheck="false">
    <select class="sort" id="sort" aria-label="Sort"><option value="useful">Most useful first</option><option value="new">Newest first</option><option value="az">A to Z</option></select>
  </div>
  <div class="chips" role="group" aria-label="Category">{chips}</div>
  <p class="count" id="count" aria-live="polite"></p>
  <ul class="doclist" id="list"></ul>
  <button class="btn btn-secondary more" id="more" type="button" hidden>Show More</button>
  <noscript><p>Turn on JavaScript to search the library.</p></noscript>
</div>
<script>
(function () {{
  var all = [], view = [], shown = 0, cat = '', STEP = 100, APP = {json.dumps(APP)}, ORDER = {json.dumps(CATEGORY_ORDER)};
  var $ = function (id) {{ return document.getElementById(id); }};
  function esc(s) {{ var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }}
  function apply() {{
    var q = $('q').value.trim().toLowerCase(), words = q.split(/\\s+/).filter(Boolean);
    view = all.filter(function (d) {{
      if (cat && d.c !== cat) return false;
      var t = d.t.toLowerCase();
      return words.every(function (w) {{ return t.indexOf(w) >= 0; }});
    }});
    var s = $('sort').value;
    if (s === 'az') view.sort(function (a, b) {{ return a.t.localeCompare(b.t); }});
    else view.sort(function (a, b) {{
      if (s === 'useful' && a.c !== b.c) return ORDER.indexOf(a.c) - ORDER.indexOf(b.c);
      return (b.d || '0').localeCompare(a.d || '0');
    }});
    shown = 0; $('list').innerHTML = ''; more();
    $('count').textContent = view.length.toLocaleString('en-IN') + (view.length === 1 ? ' document' : ' documents');
  }}
  function more() {{
    var html = '';
    view.slice(shown, shown + STEP).forEach(function (d) {{
      html += '<li class="doc"><a class="t" href="' + esc(d.u) + '" target="_blank" rel="noopener" data-track="open_document" data-doc="' +
        esc(d.t.slice(0, 100)) + '" data-category="' + esc(d.c) + '">' + esc(d.t) + '</a>' +
        '<span class="m">' + esc(d.c) + (d.y ? ' · ' + esc(d.y) : '') + ' · ' + esc(new URL(d.u).hostname.replace(/^www\\./, '')) + '</span>' +
        '<a class="ask" href="' + APP + '?q=' + encodeURIComponent('Explain this document: ' + d.t) + '" data-track="ask_about_document" data-doc="' +
        esc(d.t.slice(0, 100)) + '">Ask about this →</a></li>';
    }});
    $('list').insertAdjacentHTML('beforeend', html);
    shown += STEP; $('more').hidden = shown >= view.length;
  }}
  var timer;
  $('q').addEventListener('input', function () {{
    clearTimeout(timer); apply();
    timer = setTimeout(function () {{ var v = $('q').value.trim(); if (v.length > 2) window.track && track('library_search', {{search_term: v.slice(0, 100)}}); }}, 1200);
  }});
  $('sort').addEventListener('change', apply);
  $('more').addEventListener('click', more);
  document.querySelectorAll('.chip').forEach(function (b) {{
    b.addEventListener('click', function () {{
      cat = b.dataset.cat;
      document.querySelectorAll('.chip').forEach(function (x) {{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }});
      apply(); window.track && track('library_filter', {{category: cat || 'All'}});
    }});
  }});
  var p = new URLSearchParams(location.search); if (p.get('q')) $('q').value = p.get('q');
  fetch('docs.json').then(function (r) {{ return r.json(); }}).then(function (d) {{ all = d; apply(); }});
}})();
</script>"""
    write("library/index.html", page(f"Library of Official Documents | {NAME}",
                                     f"{len(docs):,} official Central Government rules, orders, notifications, manuals and judgments, each linked to the official copy.",
                                     "library/", body, active="Library"))
    return len(docs)


# ---------------------------------------------------------------- articles
MD = markdown.Markdown(extensions=["tables", "sane_lists"])


def md(text: str) -> str:
    out = MD.reset().convert(text or "")
    return re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener" data-track="open_citation"', out)


def load_articles() -> list[dict]:
    arts = []
    for f in sorted(glob.glob(os.path.join(SITE, "articles", "src", "*.json"))):
        try:
            a = json.load(open(f, encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print("  skipped (bad JSON):", os.path.basename(f), exc, file=sys.stderr)
            continue
        missing = [k for k in ("slug", "title", "description", "category", "answer", "sections") if not a.get(k)]
        if missing or "—" in json.dumps(a, ensure_ascii=False):
            print("  skipped:", os.path.basename(f), "missing " + ", ".join(missing) if missing else "contains an em dash", file=sys.stderr)
            continue
        a["slug"] = re.sub(r"[^a-z0-9-]+", "-", a["slug"].lower()).strip("-")
        arts.append(a)
    return arts


def build_articles(arts: list[dict]) -> None:
    by_cat: dict[str, list[dict]] = {}
    for a in arts:
        by_cat.setdefault(a["category"], []).append(a)
    for a in arts:
        url = f"{BASE}articles/{a['slug']}/"
        sections = "".join(f'<h2>{E(s["heading"])}</h2>\n{md(s["body_md"])}' for s in a["sections"])
        faqs = a.get("faqs") or []
        faq_html = ('<h2>Related Questions</h2><div class="faq">' + "".join(
            f'<details><summary>{E(f["q"])}</summary><p>{E(f["a"])}</p></details>' for f in faqs) + "</div>") if faqs else ""
        sources = a.get("sources") or []
        src_html = ('<h2>Official Sources</h2><ul class="sources">' + "".join(
            f'<li><a href="{E(s["url"])}" target="_blank" rel="noopener" data-track="open_source" data-doc="{E(s["title"][:100])}">{E(s["title"])}</a>'
            f'{" · " + E(s["issuer"]) if s.get("issuer") else ""}</li>' for s in sources if s.get("url")) + "</ul>") if sources else ""
        related = [r for r in by_cat.get(a["category"], []) if r is not a][:5]
        rel_html = ('<h2>More in ' + E(a["category"]) + '</h2><div class="related">' + "".join(
            f'<a href="{BASE}articles/{r["slug"]}/">{E(r["title"])}</a>' for r in related) + "</div>") if related else ""
        checked = a.get("last_checked") or TODAY
        schema = [
            {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["description"],
             "dateModified": checked, "datePublished": checked, "mainEntityOfPage": url,
             "author": {"@type": "Organization", "name": NAME}, "publisher": {"@type": "Organization", "name": NAME}},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Articles", "item": BASE + "articles/"},
                {"@type": "ListItem", "position": 2, "name": a["title"], "item": url}]},
        ]
        if faqs:
            schema.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": a["title"], "acceptedAnswer": {"@type": "Answer", "text": a["answer"]}}] + [
                {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]})
        body = f"""<div class="wrap narrow">
  <p class="crumbs"><a href="{BASE}articles/">Articles</a> / {E(a["category"])}</p>
  <h1>{E(a["title"])}</h1>
  <p class="meta"><span>{E(a.get("applies_to", ""))}</span><span>Checked against official documents on {pretty_date(checked)}</span></p>
  <div class="answer"><b>Short answer</b>{E(a["answer"])}</div>
  <div class="article">{sections}{faq_html}{src_html}</div>
  <div class="cta-box"><p>Have a question about your own case?</p>
    <a class="btn btn-primary" href="{APP}?q={E(json.dumps(a['title'])[1:-1])}" data-track="open_assistant" data-from="article:{E(a['slug'])}">Ask the Assistant</a></div>
  {rel_html}
  <p class="note">This article explains the official rules as published; it is not legal advice. Check the cited document, and your own department's orders, before acting.</p>
</div>"""
        write(f"articles/{a['slug']}/index.html", page(f"{a['title']} | {NAME}", a["description"], f"articles/{a['slug']}/", body,
                                                       active="Articles", head="".join(ld(s) for s in schema)))
    cats = sorted(by_cat, key=lambda c: (["Leave", "Pay and Allowances", "Conduct", "Discipline", "Pension and Retirement",
                                          "Health and Travel", "Teachers (KVS/NVS)", "Delhi Police", "Office Procedure", "Other"] + [c]).index(c))
    groups = "".join(f'<section class="cat"><h2>{E(c)}</h2>' + "".join(
        f'<a href="{BASE}articles/{a["slug"]}/">{E(a["title"])}</a>' for a in sorted(by_cat[c], key=lambda x: x["title"])) + "</section>"
        for c in cats)
    body = f"""<div class="wrap">
  <h1>Service Rule Answers</h1>
  <p class="lead">Plain-English answers to the questions Central Government employees ask most, each checked against the official rules and orders, with the rule and page cited.</p>
  <div class="cards">{groups}</div>
</div>"""
    write("articles/index.html", page(f"Service Rule Answers for Central Government Employees | {NAME}",
                                      "Plain-English answers on leave, pay, DA, conduct, discipline, pension and more, each checked against the official rules with the page cited.",
                                      "articles/", body, active="Articles"))


# ---------------------------------------------------------------- policies
def build_policies() -> None:
    g = CFG.get("grievance_officer") or {}
    contact = (f'<p><b>Grievance Officer:</b> {E(g["name"])}, <a href="mailto:{E(g["email"])}">{E(g["email"])}</a>. '
               "We reply within one month of receiving a grievance.</p>") if g.get("name") and g.get("email") else \
              "<p><b>Grievance Officer:</b> details will be published here shortly.</p>"
    model = E(CFG.get("model", "Claude"))
    privacy = f"""<div class="wrap narrow article">
  <h1>Privacy Policy</h1>
  <p class="meta">Last updated {pretty_date(TODAY)}</p>
  <p>This policy explains what {E(NAME)} collects when you use the assistant or this website, why, and what you can do about it.</p>
  <h2>What We Collect</h2>
  <ul>
    <li><b>Your Google account details</b> when you sign in: your name, email address and Google account ID. We never see your Google password.</li>
    <li><b>Your questions and the answers</b>, with the time they were asked.</li>
    <li><b>Files you attach</b> (photos, PDFs, Word files), which are stored with your question.</li>
    <li><b>Your internet (IP) address</b>, used to limit abuse and understand where use comes from.</li>
    <li><b>Website usage</b>: pages viewed and links clicked, including which documents are opened, through Google Analytics cookies.</li>
  </ul>
  <h2>Why We Collect It</h2>
  <ul>
    <li>To answer your questions and keep the conversation going.</li>
    <li>To check answers for accuracy and find documents the library is missing.</li>
    <li>To prevent misuse and keep the service running.</li>
    <li>To understand which topics and documents people need.</li>
  </ul>
  <p>We do not sell your personal data and do not use it for advertising.</p>
  <h2>Who Processes It</h2>
  <ul>
    <li><b>Anthropic</b> ({model}) and <b>Google</b> (Gemini, as a backup) generate answers from your question and attached files.</li>
    <li><b>Google</b> provides sign-in and website analytics.</li>
    <li><b>Cloudflare</b> carries traffic to our server; <b>GitHub</b> hosts this website.</li>
  </ul>
  <p>These providers may process data outside India.</p>
  <h2>How Long We Keep It</h2>
  <p>Questions, answers and attached files are kept for up to 12 months, then deleted. Account details are kept while you use the service. You can ask us to delete your data at any time.</p>
  <h2>Your Choices and Rights</h2>
  <ul>
    <li>Leave out names and personal details you don't need to share, including other people's details in documents you attach.</li>
    <li>Sign out at any time from the account menu in the assistant.</li>
    <li>Ask us for a copy of your data, to correct it, or to delete it, by writing to the Grievance Officer below.</li>
    <li>You can block analytics cookies in your browser; the site still works.</li>
  </ul>
  <h2>Who It Is For</h2>
  <p>The service is built for serving and retired government employees, and the people who advise them on service matters.</p>
  <h2>Security</h2>
  <p>Data is stored on access-controlled systems and sent over encrypted connections. No system is perfectly secure; if a breach affects you, we will tell you.</p>
  <h2>Contact and Grievances</h2>
  {contact}
  <p>If you are not satisfied with our response, you may approach the Data Protection Board of India once it accepts complaints under the Digital Personal Data Protection Act, 2023.</p>
</div>"""
    terms = f"""<div class="wrap narrow article">
  <h1>Terms of Use</h1>
  <p class="meta">Last updated {pretty_date(TODAY)}</p>
  <h2>What This Service Is</h2>
  <p>{E(NAME)} is an AI assistant that explains Indian Central Government service rules from a library of official documents. It is an independent project. It is not run by, or affiliated with, the Government of India or any department.</p>
  <h2>Not Legal Advice</h2>
  <p>Answers are written by an AI model ({model}) and are information, not legal or professional advice. They can be wrong or out of date. Check the cited rule or order, and your own department's instructions, before you rely on an answer. For a serious matter such as a penalty, a court case or a large payment, take advice from a qualified person.</p>
  <h2>Who May Use It</h2>
  <p>You must be 18 or older and sign in with your own Google account.</p>
  <h2>Acceptable Use</h2>
  <ul>
    <li>Do not upload documents you have no right to share, or other people's personal details beyond what your question needs.</li>
    <li>Do not use the service to harass anyone, break the law, or overload or attack the service.</li>
    <li>Do not present answers as official government statements.</li>
  </ul>
  <p>We may limit or suspend access that breaks these terms.</p>
  <h2>Documents and Links</h2>
  <p>Rules, orders and judgments are public documents published by their issuing authorities. Links open the official copies on those authorities' websites, which we do not control.</p>
  <h2>Availability and Changes</h2>
  <p>The service is in testing and may change, pause or stop without notice. Features may later require payment; we will tell you before anything you use becomes paid. We may update these terms; the date above shows the latest version.</p>
  <h2>Liability</h2>
  <p>To the extent the law allows, we are not liable for any loss arising from reliance on an answer or from the service being unavailable.</p>
  <h2>Law and Contact</h2>
  <p>These terms are governed by the laws of India. Questions and complaints go to the Grievance Officer named in the <a href="{BASE}privacy/">Privacy Policy</a>.</p>
</div>"""
    write("privacy/index.html", page(f"Privacy Policy | {NAME}", f"How {NAME} collects, uses and protects your data.", "privacy/", privacy))
    write("terms/index.html", page(f"Terms of Use | {NAME}", f"The terms for using {NAME}.", "terms/", terms))


# ---------------------------------------------------------------- latest notifications
NOTIF = os.path.join(ROOT, "_claude", "corpus", "central_rules", "notifications")


def build_latest() -> int:
    """Newest official orders from the notifications collection (kept current by bot/tracker/)."""
    rows = []
    for mf in glob.glob(os.path.join(NOTIF, "*", "_manifest.json")):
        try:
            for r in json.load(open(mf, encoding="utf-8")):
                if r.get("source", "").startswith("http") and r.get("date"):
                    rows.append(r)
        except Exception:
            continue
    rows.sort(key=lambda r: r["date"], reverse=True)
    rows = rows[:200]
    items = "".join(
        f'<li class="doc"><a class="t" href="{E(r["source"])}" target="_blank" rel="noopener" data-track="open_document" '
        f'data-doc="{E(r["title"][:100])}" data-category="Latest notifications">{E(r.get("subject") or r["title"])}</a>'
        f'<span class="m">{E(r.get("issuer", ""))}{" · " + E(r["number"]) if r.get("number") else ""} · {pretty_date(r["date"])}</span>'
        f'<a class="ask" href="{APP}?q={E(json.dumps("Explain this order: " + r["title"])[1:-1])}" data-track="ask_about_document" '
        f'data-doc="{E(r["title"][:100])}">Ask about this →</a></li>' for r in rows)
    body = f"""<div class="wrap">
  <h1>Latest Notifications</h1>
  <p class="lead">New office memoranda, orders and notifications from DoPT, the Department of Expenditure, the Department of Pension and Pensioners' Welfare, CGHS and the GPF interest notifications, checked daily. Each link opens the official copy. Updated {pretty_date(TODAY)}.</p>
  <ul class="doclist">{items}</ul>
  <p class="note">Showing the newest {len(rows)}. Older orders are in the <a href="{BASE}library/">Library</a>.</p>
</div>"""
    write("latest/index.html", page(f"Latest Central Government Notifications and Orders | {NAME}",
                                    "New DoPT, Department of Expenditure, pension and CGHS orders for Central Government employees, checked daily, with links to the official copies.",
                                    "latest/", body, active="Latest"))
    return len(rows)


# ---------------------------------------------------------------- requests and feedback
def build_feedback() -> None:
    body = f"""<div class="wrap narrow article">
  <h1>Tell Us What You Want</h1>
  <p class="lead">A document you need, a feature you wish it had, an answer that was wrong, or anything else. Every message is read.</p>
  <form id="fb" style="display:grid;gap:14px;max-width:560px">
    <label>What is it about?
      <select id="kind" class="search" style="width:100%;margin-top:6px">
        <option value="document">Add a document or order</option>
        <option value="feature">A new feature (e.g. fill a form for me, a calculator)</option>
        <option value="wrong_answer">An answer was wrong</option>
        <option value="complaint">A complaint</option>
        <option value="other">Something else</option>
      </select></label>
    <label>Tell us more
      <textarea id="text" required rows="6" class="search" style="width:100%;height:auto;padding:12px 16px;margin-top:6px" placeholder="What would you like to happen?"></textarea></label>
    <label>Phone or email, if you want a reply (optional)
      <input id="contact" class="search" style="width:100%;margin-top:6px" autocomplete="email"></label>
    <button class="btn btn-primary" type="submit" style="justify-self:start">Send</button>
    <p id="msg" class="muted" aria-live="polite"></p>
  </form>
  <p class="note">We use this only to improve the service. See the <a href="{BASE}privacy/">Privacy Policy</a>.</p>
</div>
<script>
document.getElementById('fb').addEventListener('submit', async function (e) {{
  e.preventDefault();
  var msg = document.getElementById('msg'), text = document.getElementById('text').value.trim();
  if (!text) return;
  msg.textContent = 'Sending…';
  try {{
    var c = await (await fetch('{APP}config.json?t=' + Date.now(), {{cache: 'no-store'}})).json();
    var body = JSON.stringify({{kind: document.getElementById('kind').value, text: text,
      contact: document.getElementById('contact').value, page: 'website'}});
    var ok = false;
    for (var s of [c.server, c.fallback].filter(Boolean)) {{
      try {{ var r = await fetch(s + '/v1/feedback', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: body}});
            if (r.ok) {{ ok = true; break; }} }} catch (err) {{}}
    }}
    msg.textContent = ok ? 'Thank you. It has reached the team.' : 'Could not send right now. Please try again later.';
    if (ok) {{ document.getElementById('text').value = ''; window.track && track('feedback_sent', {{kind: document.getElementById('kind').value}}); }}
  }} catch (err) {{ msg.textContent = 'Could not send right now. Please try again later.'; }}
}});
</script>"""
    write("feedback/index.html", page(f"Tell Us What You Want | {NAME}", f"Request a document or feature, or report a wrong answer, for {NAME}.",
                                      "feedback/", body))


# ---------------------------------------------------------------- active users (shown when the laptop is off)
def build_stats() -> None:
    sys.path.insert(0, os.path.join(ROOT, "bot"))
    import usage
    write("stats.json", json.dumps(usage.active_users()))


# ---------------------------------------------------------------- sitemap
def build_sitemap(arts: list[dict]) -> None:
    urls = [("", TODAY), ("latest/", TODAY), ("library/", TODAY), ("articles/", TODAY), ("feedback/", TODAY), ("privacy/", TODAY), ("terms/", TODAY)] + \
           [(f"articles/{a['slug']}/", a.get("last_checked") or TODAY) for a in arts]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"  <url><loc>{E(BASE + u)}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n")


if __name__ == "__main__":
    n = build_library()
    latest = build_latest()
    arts = load_articles()
    build_articles(arts)
    build_policies()
    build_feedback()
    build_stats()
    build_sitemap(arts)
    print(f"library: {n} documents · latest: {latest} · articles: {len(arts)} · policies · sitemap")
