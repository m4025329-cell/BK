#!/usr/bin/env python3
"""Генератор статического сайта с курсами валют (программное SEO).

Запуск:  python3 generate.py            # живые курсы (open.er-api.com, без ключа)
         python3 generate.py --offline  # тестовые курсы, без сети
Результат в папке dist/.
"""
import html, json, shutil, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "dist"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

CURRENCIES = {
    "USD": "Доллар США", "EUR": "Евро", "RUB": "Российский рубль", "UAH": "Украинская гривна",
    "KZT": "Казахстанский тенге", "BYN": "Белорусский рубль", "PLN": "Польский злотый",
    "GBP": "Британский фунт", "CNY": "Китайский юань", "TRY": "Турецкая лира",
    "CZK": "Чешская крона", "CHF": "Швейцарский франк", "JPY": "Японская иена",
    "GEL": "Грузинский лари", "AMD": "Армянский драм", "AZN": "Азербайджанский манат",
    "UZS": "Узбекский сум", "MDL": "Молдавский лей", "AED": "Дирхам ОАЭ",
    "THB": "Таиландский бат", "INR": "Индийская рупия", "CAD": "Канадский доллар",
}
AMOUNTS = [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000]
SAMPLE = {"USD": 1, "EUR": 0.92, "RUB": 92, "UAH": 41, "KZT": 480, "BYN": 3.27, "PLN": 4.0,
          "GBP": 0.79, "CNY": 7.2, "TRY": 34, "CZK": 23, "CHF": 0.88, "JPY": 150, "GEL": 2.7,
          "AMD": 388, "AZN": 1.7, "UZS": 12700, "MDL": 17.8, "AED": 3.67, "THB": 35,
          "INR": 83, "CAD": 1.36}


def fetch_rates(offline):
    if offline:
        return SAMPLE, "тестовые данные"
    req = urllib.request.Request("https://open.er-api.com/v6/latest/USD",
                                 headers={"User-Agent": "rates-site/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("result") != "success":
        raise SystemExit("API error: %r" % data)
    rates = {c: data["rates"][c] for c in CURRENCIES if c in data["rates"]}
    if len(rates) < 10:
        raise SystemExit("Слишком мало валют в ответе API")
    return rates, data.get("time_last_update_utc", "")


def fmt(x):
    if x >= 100:
        s = f"{x:,.2f}"
    elif x >= 1:
        s = f"{x:,.4f}"
    else:
        s = f"{x:,.6f}"
    return s.replace(",", " ").rstrip("0").rstrip(".") if "." in s else s


def monetization():
    parts = []
    if CFG["affiliate_url"]:
        parts.append(f'<div class="aff"><p>{html.escape(CFG["affiliate_text"])}</p>'
                     f'<a rel="sponsored nofollow noopener" target="_blank" href="{html.escape(CFG["affiliate_url"])}">'
                     f'{html.escape(CFG["affiliate_label"])}</a></div>')
    if CFG["affiliate_banner_html"]:
        parts.append(CFG["affiliate_banner_html"])
    if CFG["adsense_client"]:
        parts.append(f'<ins class="adsbygoogle" style="display:block" data-ad-client="{CFG["adsense_client"]}" '
                     'data-ad-format="auto" data-full-width-responsive="true"></ins>'
                     '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>')
    return "\n".join(parts)


LOGO = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.6-1-1.7-1.5-3-1.5-1.7 0-3 .9-3 2.2'
        ' 0 3 6 1.6 6 4.6 0 1.3-1.3 2.2-3 2.2-1.4 0-2.5-.6-3.1-1.6M12 6v2m0 8v2"/></svg>')
SWAP = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M7 4v14m0 0-3-3m3 3 3-3M17 20V6m0 0-3 3m3-3 3 3"/></svg>')
SEARCH = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>')


def page(title, desc, path, body, jsonld=None):
    url = CFG["site_url"].rstrip("/") + path
    head_extra = ""
    if CFG["adsense_client"]:
        head_extra += (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='
                       f'{CFG["adsense_client"]}" crossorigin="anonymous"></script>')
    if CFG["analytics_id"]:
        a = CFG["analytics_id"]
        head_extra += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={a}"></script>'
                       f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}'
                       f'gtag("js",new Date());gtag("config","{a}");</script>')
    if jsonld:
        head_extra += f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#1e40af">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{BASE}/style.css">
{head_extra}</head><body>
<header class="top"><div class="wrap">
<a class="logo" href="{BASE}/">{LOGO}{html.escape(CFG['site_name'])}</a>
<nav class="top" aria-label="Основная"><a href="{BASE}/usd-rub/">USD</a><a href="{BASE}/eur-rub/">EUR</a><a href="{BASE}/usd-kzt/">KZT</a><a href="{BASE}/usd-uah/">UAH</a></nav>
</div></header>
<main><div class="wrap">{body}</div></main>
<footer class="bot"><div class="wrap"><p>Курсы носят справочный характер и не являются офертой. Источник: open.er-api.com. © {html.escape(CFG['site_name'])}</p></div></footer>
</body></html>"""


CSS = """
:root{--primary:#1e40af;--primary-h:#1d4ed8;--accent:#047857;--bg:#f8fafc;--card:#fff;--fg:#0f172a;--muted:#475569;--border:#e2e8f0;--chip:#eff6ff;--radius:14px;--shadow:0 1px 2px rgba(15,23,42,.06),0 4px 14px rgba(15,23,42,.05)}
@media (prefers-color-scheme:dark){:root{--primary:#60a5fa;--primary-h:#93c5fd;--accent:#34d399;--bg:#0b1220;--card:#131c2e;--fg:#f1f5f9;--muted:#94a3b8;--border:#243049;--chip:#16233d;--shadow:none}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--primary);text-underline-offset:3px}a:hover{color:var(--primary-h)}
:focus-visible{outline:3px solid var(--primary);outline-offset:2px;border-radius:6px}
.wrap{max-width:960px;margin:0 auto;padding:0 16px}
header.top{background:var(--card);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:5}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;height:60px}
.logo{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.05rem;color:var(--fg);text-decoration:none}
.logo svg{width:28px;height:28px;color:var(--primary)}
nav.top a{margin-left:16px;font-size:.92rem;font-weight:500;text-decoration:none;color:var(--muted)}
nav.top a:hover{color:var(--primary)}
main{padding:28px 0 48px}
h1{font-size:clamp(1.55rem,4.5vw,2.2rem);line-height:1.2;margin:.2em 0 .3em;letter-spacing:-.02em}
h2{font-size:1.2rem;margin:1.8em 0 .7em}
.lead{color:var(--muted);margin:0 0 20px}
.crumbs{font-size:.85rem;color:var(--muted);margin-bottom:6px}.crumbs a{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
.num{font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}
.rate{font-size:clamp(2rem,8vw,3rem);font-weight:700;letter-spacing:-.02em;line-height:1.1}
.rate small{font-size:.45em;font-weight:500;color:var(--muted);margin-left:6px}
.sub{color:var(--muted);margin-top:8px;font-size:.95rem}
.conv{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:end;margin-top:6px}
.conv label{display:block;font-size:.8rem;font-weight:600;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em}
.field{display:flex;align-items:center;border:1px solid var(--border);border-radius:12px;background:var(--bg);padding:0 14px;height:56px}
.field:focus-within{border-color:var(--primary);box-shadow:0 0 0 3px color-mix(in srgb,var(--primary) 25%,transparent)}
.field input,.field output{flex:1;min-width:0;border:0;background:transparent;color:var(--fg);font:inherit;font-size:1.25rem;font-weight:600;outline:0;width:100%}
.field span{color:var(--muted);font-weight:600;margin-left:8px}
.swap{display:flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:50%;background:var(--chip);color:var(--primary);text-decoration:none;margin-bottom:4px;transition:background .2s,transform .2s}
.swap:hover{background:var(--primary);color:#fff;transform:rotate(180deg)}
.swap svg{width:22px;height:22px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th{font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:2px solid var(--border)}
td{padding:9px 10px;border-bottom:1px solid var(--border);white-space:nowrap}
td:last-child,th:last-child{text-align:right}
tbody tr:hover{background:var(--chip)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border:1px solid var(--border);border-radius:999px;background:var(--card);color:var(--fg);text-decoration:none;font-size:.92rem;font-weight:500;transition:border-color .15s,background .15s}
.chip:hover{border-color:var(--primary);background:var(--chip);color:var(--primary)}
.chip b{margin-left:8px;font-variant-numeric:tabular-nums;color:var(--muted);font-weight:500}
.pop{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.pop a{display:block;padding:16px;border:1px solid var(--border);border-radius:var(--radius);background:var(--card);box-shadow:var(--shadow);text-decoration:none;color:var(--fg);transition:border-color .15s,transform .15s}
.pop a:hover{border-color:var(--primary);transform:translateY(-2px)}
.pop .pair{font-size:.85rem;font-weight:600;color:var(--muted)}
.pop .val{font-size:1.5rem;font-weight:700;margin-top:4px}
.search{position:relative;margin:18px 0 6px}
.search input{width:100%;height:52px;padding:0 16px 0 46px;border:1px solid var(--border);border-radius:12px;background:var(--card);color:var(--fg);font:inherit;font-size:1rem}
.search svg{position:absolute;left:14px;top:14px;width:24px;height:24px;color:var(--muted)}
.aff{background:var(--chip);border:1px solid var(--border);border-left:4px solid var(--accent);padding:16px 18px;margin:20px 0;border-radius:var(--radius)}
.aff p{margin:0 0 10px}
.aff a{display:inline-flex;align-items:center;min-height:44px;background:var(--accent);color:#fff;padding:0 18px;border-radius:10px;text-decoration:none;font-weight:600}
.aff a:hover{filter:brightness(1.1);color:#fff}
footer.bot{border-top:1px solid var(--border);color:var(--muted);font-size:.85rem;padding:22px 0}
@media (max-width:640px){.conv{grid-template-columns:1fr}.swap{margin:0 auto;transform:rotate(90deg)}.swap:hover{transform:rotate(270deg)}.grid2{grid-template-columns:1fr}nav.top{display:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}.swap:hover,.pop a:hover{transform:none}}
"""


BASE = ""


def main():
    global BASE
    offline = "--offline" in sys.argv
    BASE = "/" + CFG["site_url"].rstrip("/").split("/", 3)[3] if CFG["site_url"].rstrip("/").count("/") > 2 else ""
    rates, updated = fetch_rates(offline)
    codes = [c for c in CURRENCIES if c in rates]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        from email.utils import parsedate_to_datetime
        updated_h = parsedate_to_datetime(updated).strftime("%d.%m.%Y %H:%M UTC")
    except Exception:
        updated_h = updated
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    mon = monetization()
    urls = ["/"]

    # страницы пар
    for a in codes:
        for b in codes:
            if a == b:
                continue
            r = rates[b] / rates[a]
            name_a, name_b = CURRENCIES[a], CURRENCIES[b]
            rows = "".join(f"<tr><td>{n:,} {a}</td><td>{fmt(n * r)} {b}</td></tr>".replace(",", " ")
                           for n in AMOUNTS)
            rev = "".join(f"<tr><td>{n:,} {b}</td><td>{fmt(n / r)} {a}</td></tr>".replace(",", " ")
                          for n in AMOUNTS)
            rows = "".join(f"<tr><td>{n:,} {a}</td><td>{fmt(n * r)} {b}</td></tr>".replace(",", "\u00a0") for n in AMOUNTS)
            rev = "".join(f"<tr><td>{n:,} {b}</td><td>{fmt(n / r)} {a}</td></tr>".replace(",", "\u00a0") for n in AMOUNTS)
            others = "".join(f'<a class="chip" href="{BASE}/{a.lower()}-{x.lower()}/">{a} → {x}</a>'
                             for x in codes if x not in (a, b))
            body = f"""<div class="crumbs"><a href="{BASE}/">Главная</a> › {a} → {b}</div>
<h1>{a} в {b}: курс на {today}</h1>
<p class="lead">{name_a} к валюте «{name_b}»</p>
<section class="card" aria-label="Курс">
<div class="rate num">1 {a} = {fmt(r)}<small>{b}</small></div>
<div class="sub num">Обратный курс: 1 {b} = {fmt(1 / r)} {a} · обновляется ежедневно</div>
</section>
{mon}
<h2>Конвертер {a} → {b}</h2>
<section class="card">
<div class="conv">
<div><label for="v">Сумма</label><div class="field"><input id="v" type="text" inputmode="decimal" value="100" autocomplete="off"><span>{a}</span></div></div>
<a class="swap" href="{BASE}/{b.lower()}-{a.lower()}/" aria-label="Поменять направление: {b} в {a}" title="Поменять направление">{SWAP}</a>
<div><label for="o">Получите</label><div class="field"><output id="o" for="v" class="num">—</output><span>{b}</span></div></div>
</div></section>
<script>var R={r!r};var v=document.getElementById('v'),o=document.getElementById('o');function u(){{var x=parseFloat(v.value.replace(/\s/g,'').replace(',','.'));o.textContent=isNaN(x)?'—':(x*R).toLocaleString('ru-RU',{{maximumFractionDigits:R<1?6:4}})}}v.oninput=u;u();</script>
<div class="grid2">
<div><h2>{a} → {b}</h2><div class="card tbl"><table><thead><tr><th>{a}</th><th>{b}</th></tr></thead><tbody>{rows}</tbody></table></div></div>
<div><h2>{b} → {a}</h2><div class="card tbl"><table><thead><tr><th>{b}</th><th>{a}</th></tr></thead><tbody>{rev}</tbody></table></div></div>
</div>
<h2>Другие направления {a}</h2><div class="chips">{others}</div>"""
            faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{
                "@type": "Question", "name": f"Сколько будет 1 {a} в {b}?",
                "acceptedAnswer": {"@type": "Answer", "text": f"На {today} 1 {a} = {fmt(r)} {b}."}}]}
            d = OUT / f"{a.lower()}-{b.lower()}"
            d.mkdir()
            (d / "index.html").write_text(page(
                f"{a} в {b} — курс на {today}, конвертер валют",
                f"Курс {a} к {b} сегодня: 1 {a} = {fmt(r)} {b}. Конвертер и таблицы сумм.",
                f"/{a.lower()}-{b.lower()}/", body, faq), encoding="utf-8")
            urls.append(f"/{a.lower()}-{b.lower()}/")

    # главная
    pop = ["USD", "EUR", "RUB", "UAH", "KZT", "PLN", "GBP", "CNY", "TRY"]
    featured = [("USD", "RUB"), ("EUR", "RUB"), ("USD", "KZT"), ("USD", "UAH"), ("EUR", "USD"), ("USD", "PLN"),
                ("USD", "TRY"), ("CNY", "RUB")]
    cards = "".join(f'<a href="{BASE}/{a.lower()}-{b.lower()}/"><div class="pair">{a} → {b}</div>'
                    f'<div class="val num">{fmt(rates[b] / rates[a])}</div></a>'
                    for a, b in featured if a in rates and b in rates)
    sections = "".join(
        f'<section class="grp"><h2>{a} — {html.escape(CURRENCIES[a])}</h2><div class="chips">' +
        "".join(f'<a class="chip" data-s="{a} {b} {html.escape(CURRENCIES[b]).lower()}" '
                f'href="{BASE}/{a.lower()}-{b.lower()}/">{a} → {b}<b class="num">{fmt(rates[b] / rates[a])}</b></a>'
                for b in codes if b != a) + "</div></section>" for a in pop if a in codes)
    search_js = ("<script>var q=document.getElementById('q');q.oninput=function(){var t=q.value.trim().toLowerCase();"
                 "document.querySelectorAll('.chip[data-s]').forEach(function(c){c.style.display=!t||c.dataset.s.toLowerCase()"
                 ".indexOf(t)>-1?'':'none'});document.querySelectorAll('.grp').forEach(function(g){g.style.display="
                 "g.querySelector('.chip:not([style*=none])')?'':'none'})}</script>")
    (OUT / "index.html").write_text(page(
        f"{CFG['site_name']} — конвертер {', '.join(pop[:4])} и других валют",
        "Актуальные курсы валют и онлайн-конвертер. Обновляется ежедневно.", "/",
        f"<h1>{html.escape(CFG['site_name'])}</h1><p class=\"lead\">Актуальные курсы и конвертер. Обновлено: {html.escape(updated_h)}</p>"
        f'<div class="search">{SEARCH}<input id="q" type="search" placeholder="Найти валюту: USD, евро, тенге…" '
        f'aria-label="Поиск валюты" autocomplete="off"></div>'
        f"{mon}<h2>Популярные курсы</h2><div class=\"pop\">{cards}</div>{sections}{search_js}"),
        encoding="utf-8")

    # sitemap / robots / ads.txt
    site = CFG["site_url"].rstrip("/")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
        "".join(f"<url><loc>{site}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site}/sitemap.xml\n")
    if CFG["adsense_client"]:
        pub = CFG["adsense_client"].replace("ca-", "")
        (OUT / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n")
    (OUT / ".nojekyll").write_text("")
    print(f"Сгенерировано страниц: {len(urls)} -> {OUT}")


if __name__ == "__main__":
    main()
