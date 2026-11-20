"""Build one static, indexable page per story from index.html.
Run: python3 tools/build_pages.py  (needs Playwright + Chrome)."""
import json, re, html, pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
U = 'https://fursaway.netlify.app'
src = (ROOT / 'index.html').read_text()
head_css = re.search(r'<style>.*?</style>', src, re.S).group(0)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
    pg = b.new_page()
    pg.goto((ROOT / 'index.html').as_uri())
    ids = pg.evaluate("[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).map(h=>(h.match(/^#story-([a-z0-9]+)$/)||h.match(/^\\/stories\\/([a-z0-9]+)\\.html$/)||[])[1]).filter(Boolean)")
    ids = sorted(set(ids))
    out = ROOT / 'stories'; out.mkdir(exist_ok=True)
    urls = []
    for sid in ids:
        pg.goto((ROOT / 'index.html').as_uri() + '#story-' + sid); pg.wait_for_timeout(150)
        art = pg.eval_on_selector('#story', 'e => e.innerHTML')
        title = pg.eval_on_selector('#story h1', 'e => e.textContent')
        dek = pg.eval_on_selector('#story .dek', 'e => e.textContent')
        art = art.replace('href="#news"', 'href="/#news"').replace('href="#story-', 'href="/stories/').replace('"><b class="sans">Read our', '"><b class="sans">Read our')
        art = re.sub(r'href="/stories/([a-z0-9]+)"', r'href="/stories/\1.html"', art)
        ld = {"@context":"https://schema.org","@type":"NewsArticle","headline":title,"description":dek,
              "datePublished":"2026-11-20","dateModified":"2026-11-20","url":f"{U}/stories/{sid}.html",
              "image":f"{U}/og-image.png","publisher":{"@type":"NewsMediaOrganization","name":"Fursaway","logo":{"@type":"ImageObject","url":f"{U}/apple-touch-icon.png"}}}
        page = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Fursaway</title>
<meta name="description" content="{html.escape(dek)}">
<link rel="canonical" href="{U}/stories/{sid}.html">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><meta name="theme-color" content="#6d1a2e">
<meta property="og:type" content="article"><meta property="og:site_name" content="Fursaway">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(dek)}">
<meta property="og:url" content="{U}/stories/{sid}.html"><meta property="og:image" content="{U}/og-image.png"><meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld)}</script>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,700&display=swap" rel="stylesheet">
{head_css}</head><body>
<header class="wrap mast"><a class="logo" href="/">Fursaway<small>Opportunities, education and travel, verified.</small></a></header>
<nav aria-label="Sections"><div class="wrap"><a href="/#opportunities">Opportunities</a><a href="/#news">News</a><a href="/#travel">Travel and visas</a><a href="/#tourism">Tourism</a><a href="/#apply">How to apply</a><a href="/#newsroom">Newsroom</a><a href="/#standards">Standards</a></div></nav>
<main><div class="band wrap"><article class="story">{art}</article></div></main>
<footer><div class="wrap"><div><b>Fursaway</b><p>Independent service journalism on study opportunities, applications and travel.</p></div><div><p>Produced by an AI newsroom with a fact-check desk and an editor-in-chief. Always confirm a deadline on the official page before you apply.</p><p>© 2026 Fursaway</p></div></div></footer>
</body></html>'''
        (out / f'{sid}.html').write_text(page); urls.append(f'{U}/stories/{sid}.html')
    b.close()
sm = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      f'  <url><loc>{U}/</loc><lastmod>2026-11-20</lastmod><changefreq>daily</changefreq></url>']
sm += [f'  <url><loc>{u}</loc><lastmod>2026-11-20</lastmod></url>' for u in urls]
sm.append('</urlset>')
(ROOT / 'sitemap.xml').write_text('\n'.join(sm) + '\n')
print(len(urls), 'story pages')
