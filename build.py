#!/usr/bin/env python3
"""Minimal static blog builder.

Reads content/ (site.json, pages/, posts/*.md) and writes plain HTML at the
repository root, so GitHub Pages can serve it with no build step.
"""

import html
import json
import os
import re
import shutil
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
POSTS_DIR = os.path.join(CONTENT, "posts")
SITE = json.load(open(os.path.join(CONTENT, "site.json"), encoding="utf-8"))

CJK = r"\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"


# ── markdown ────────────────────────────────────────────────────────────

def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img alt="\1" src="\2">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def paragraph(lines):
    text = " ".join(lines)
    text = re.sub(r"(?<=[%s])\s+(?=[%s])" % (CJK, CJK), "", text)
    return inline(text.strip())


def markdown(src):
    out, lines, i = [], src.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="language-%s"' % lang if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, html.escape("\n".join(buf))))
            continue

        if not stripped:
            i += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1)) + 1
            out.append("<h%d>%s</h%d>" % (level, inline(heading.group(2)), level))
            i += 1
            continue

        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % paragraph(buf))
            continue

        if re.match(r"^[-*]\s+", stripped):
            buf = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                buf.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x) for x in buf))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            buf = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                buf.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % inline(x) for x in buf))
            continue

        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,3}\s|[-*]\s|\d+\.\s|>|```|-{3,}$)", lines[i].strip()
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % paragraph(buf))
    return "\n".join(out)


# ── content ─────────────────────────────────────────────────────────────

def split_front_matter(raw):
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end < 0:
        return {}, raw
    head = raw[3:end].strip("\n")
    body = raw[end + 4:]
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body.lstrip("\n")


def load_posts():
    posts = []
    for name in sorted(os.listdir(POSTS_DIR)):
        if not name.endswith(".md"):
            continue
        raw = open(os.path.join(POSTS_DIR, name), encoding="utf-8").read()
        meta, body = split_front_matter(raw)
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name[:-3])
        posts.append({
            "slug": slug,
            "title": meta.get("title", slug),
            "date": meta.get("date", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "summary": meta.get("summary", ""),
            "html": markdown(body),
            "body": body,
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def reading_minutes(post):
    text = re.sub(r"\s+", "", post["body"])
    chars = len(re.findall(r"[%s]" % CJK, text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    return max(1, round(chars / 380 + words / 220))


def zh_date(iso, dot=False):
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
    except ValueError:
        return iso
    return d.strftime("%Y.%m.%d") if dot else d.strftime("%Y 年 %m 月 %d 日")


# ── layout ──────────────────────────────────────────────────────────────

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' fill='%23000'/%3E"
    "%3Ctext x='16' y='22' font-family='Helvetica,Arial' font-size='16' font-weight='600'"
    " fill='%23fff' text-anchor='middle'%3EZ%3C/text%3E%3C/svg%3E"
)

NAV = "".join(
    '<a href="%s"%s>%s</a>' % (
        item["href"],
        ' aria-current="page"' if item["href"].endswith("about.html") and item.get("_current") else "",
        item["label"],
    )
    for item in SITE["nav"]
)


def layout(title, description, body, canonical="/", current=""):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (
            item["href"],
            ' aria-current="page"' if current and item["href"].endswith(current) else "",
            item["label"],
        )
        for item in SITE["nav"]
    )
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{description_tag}
<link rel="canonical" href="{site}{canonical}">
<link rel="alternate" type="application/rss+xml" title="{title}" href="/feed.xml">
<link rel="icon" href="{favicon}">
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:title" content="{title}">
{description_tag}
<meta property="og:type" content="{ogtype}">
<meta property="og:url" content="{site}{canonical}">
</head>
<body>
<header class="site-header">
  <div class="inner">
    <a class="brand" href="/">{title}</a>
    <nav class="nav">{nav}</nav>
  </div>
</header>
{body}
<footer class="site-footer">
  <span>© {year}</span>
  <nav>
    <a href="/feed.xml">RSS</a>
    <a href="/#writing">Writing</a>
  </nav>
</footer>
</body>
</html>
""".format(
        title=title,
        description_tag=(
            '<meta name="description" content="%s">\n<meta property="og:description" content="%s">'
            % (html.escape(description), html.escape(description))
            if description else ""),
        site=SITE["url"],
        canonical=canonical,
        favicon=FAVICON,
        ogtype="article" if canonical.startswith("/posts/") else "website",
        nav=nav,
        body=body,
        year="2026",
    )


def index_page(posts):
    if posts:
        rows = []
        for post in posts:
            rows.append(
                """      <li class="post-row">
        <a href="/posts/{slug}.html">
          <time class="date" datetime="{iso}">{date}</time>
          <div>
            <h3>{title}</h3>
            <p>{summary}</p>
          </div>
          <span class="arrow" aria-hidden="true">→</span>
        </a>
      </li>""".format(
                    slug=post["slug"],
                    iso=post["date"],
                    date=zh_date(post["date"], dot=True),
                    title=html.escape(post["title"]),
                    summary=html.escape(post["summary"]),
                )
            )
        listing = """  <section id="writing" class="archive">
    <div class="section-head">
      <h2>Writing</h2>
      <span class="count">{count}</span>
    </div>
    <ul class="post-list">
{rows}
    </ul>
  </section>""".format(count=len(posts), rows="\n".join(rows))
    else:
        listing = """  <section id="writing" class="archive">
    <div class="section-head">
      <h2>Writing</h2>
      <span class="count">0</span>
    </div>
    <p class="empty">—</p>
  </section>"""
    body = """<main class="archive-main">
{listing}
</main>""".format(listing=listing)
    return layout(SITE["title"], "", body, "/")


def post_page(posts, index):
    post = posts[index]
    prev_post = posts[index - 1] if index > 0 else None
    next_post = posts[index + 1] if index + 1 < len(posts) else None
    nav = []
    if prev_post:
        nav.append('<a href="/posts/%s.html"><span>Newer</span>%s</a>' % (prev_post["slug"], html.escape(prev_post["title"])))
    else:
        nav.append("<span></span>")
    if next_post:
        nav.append('<a href="/posts/%s.html" style="text-align:right"><span>Older</span>%s</a>' % (next_post["slug"], html.escape(next_post["title"])))
    meta = " · ".join([zh_date(post["date"]), "%d 分钟读完" % reading_minutes(post)] + post["tags"])
    body = """<main>
  <article class="article">
    <a class="back" href="/#writing">← Writing</a>
    <h1>{title}</h1>
    <div class="post-meta">{meta}</div>
    <div class="prose">
{html}
    </div>
    <nav class="post-nav">
{nav}
    </nav>
  </article>
</main>""".format(title=html.escape(post["title"]), meta=html.escape(meta), html=post["html"], nav="\n      ".join(nav))
    return layout(
        "%s — %s" % (post["title"], SITE["title"]),
        post["summary"] or SITE["lede"],
        body,
        "/posts/%s.html" % post["slug"],
    )


def feed(posts):
    items = []
    for post in posts:
        url = "%s/posts/%s.html" % (SITE["url"], post["slug"])
        items.append(
            "  <item>\n    <title>%s</title>\n    <link>%s</link>\n    <guid>%s</guid>\n"
            "    <pubDate>%s</pubDate>\n    <description>%s</description>\n  </item>"
            % (
                html.escape(post["title"]),
                url,
                url,
                datetime.strptime(post["date"], "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0800"),
                html.escape(post["summary"]),
            )
        )
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{title}</title>
  <link>{site}</link>
  <description>{title}</description>
  <language>zh-CN</language>
{items}
</channel>
</rss>
""".format(title=SITE["title"], site=SITE["url"], items="\n".join(items))


def sitemap(posts):
    urls = ["/"] + ["/posts/%s.html" % p["slug"] for p in posts]
    body = "".join("  <url><loc>%s%s</loc></url>\n" % (SITE["url"], u) for u in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % body


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main():
    posts = load_posts()
    write("index.html", index_page(posts))
    for i, post in enumerate(posts):
        write(os.path.join("posts", post["slug"] + ".html"), post_page(posts, i))
    write("feed.xml", feed(posts))
    write("sitemap.xml", sitemap(posts))
    write(".nojekyll", "")
    print("built %d posts" % len(posts))


if __name__ == "__main__":
    main()
