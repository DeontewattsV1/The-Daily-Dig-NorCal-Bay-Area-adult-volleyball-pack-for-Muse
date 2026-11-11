#!/usr/bin/env python3
"""The Daily Dig aggregator – NorCal / Bay Area adult volleyball.

Pulls every feed in feeds.csv (RSS/Atom/ICS), scrapes public Reclub club pages,
Heylo group pages and Meetup search pages listed in sources.json, re-checks the
official program pages in sources.json for changes (and retries city pages that
return 403 through the public r.jina.ai reader), filters for adult-volleyball
relevance, de-duplicates, scores recency + relevance, and writes:

  out/daily_dig.json   machine-readable digest for Muse
  out/daily_dig.rss    merged RSS 2.0 feed (subscribe / host it)
  out/daily_dig.md     human-readable digest

Standard library only (Python 3.9+). Usage:
  python3 daily_dig.py                 # full run
  python3 daily_dig.py --no-watch      # skip page-change checks
  python3 daily_dig.py --out out --days 14 --max-items 300
Privacy: never stores attendee names, payment handles (Venmo/Zelle/CashApp),
or phone numbers from community pages.
"""
import argparse, csv, hashlib, html, json, os, re, sys, time
import urllib.request, urllib.error, concurrent.futures as cf
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime, format_datetime
from xml.etree import ElementTree as ET
try:
    from zoneinfo import ZoneInfo
    PT = ZoneInfo("America/Los_Angeles")
except Exception:  # pragma: no cover
    PT = timezone(timedelta(hours=-8))

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 DailyDig/1.0"
NOW = datetime.now(timezone.utc)

# ---------------- relevance model ----------------
VB = re.compile(r"volley|\bvball\b|\bvb\b|reverse co-?ed|revco", re.I)
NOT_VB = re.compile(r"spikeball|roundnet|pickleball only", re.I)
OUT_OF_AREA = re.compile(r"Oakland University|Golden Grizzlies|Green Bay|Michigan|Tennessee|Youngstown|Milwaukee|Hawaii|Rainbow Wahine|Mountain West|Long Beach|Italian|Conegliano|Brazil|Poland|Big Ten|SEC\b|Texas|Florida|Nebraska|Wisconsin", re.I)
ADULT = re.compile(r"\badult|18\+|21\+|co-?ed|reverse|revco|men'?s|women'?s|open gym|drop[- ]?in|pick-?up|league|tournament|clinic|doubles|triples|quads|6s\b|4s\b|grass|beach|sand|social|rec\b|\bB/BB|\bBB\b|\bAA\b|\bA\b level", re.I)
YOUTH = re.compile(r"high school|\bhs\b|varsity|\bjv\b|freshman|junior varsity|middle school|\bU1[0-8]\b|\b1[0-8]u\b|youth|kids|girls'? |boys'? |tween|cif|ncs|maxpreps|prep\b|club tryouts?|WPIAL|class \d?A+\b|group \d|state (volleyball )?tournament|section final|CCS|NCS|sac-joaquin|maxpreps|catholic|township|semifinal|quarterfinal", re.I)
COLLEGE = re.compile(r"\bNCAA\b|Stanford|Cal Bears|\bCal\b|San Jose State|Spartans|USF Dons|Saint Mary|Gaels|Pacific Tigers|Sac State|Hornets|UC Davis|Aggies|Santa Clara Broncos", re.I)
PLACES = ["bay area","san francisco","sf ","oakland","berkeley","alameda","emeryville","san jose","santa clara","sunnyvale","mountain view","palo alto","menlo park","redwood city","san mateo","daly city","south san francisco","pacifica","half moon bay","fremont","hayward","san lorenzo","union city","milpitas","campbell","cupertino","los gatos","walnut creek","concord","pleasant hill","pleasanton","livermore","dublin","san ramon","danville","antioch","pittsburg","richmond","el cerrito","marin","san rafael","novato","napa","sonoma","santa rosa","petaluma","vallejo","benicia","vacaville","fairfield","sacramento","rancho cordova","elk grove","folsom","roseville","rocklin","davis","stockton","tracy","manteca","santa cruz","monterey","norcal","northern california","east bay","south bay","peninsula","ocean beach","crown beach","main beach","stanford"]
PROMO_OK = re.compile(r"open gym|drop[- ]?in|pick-?up|league|tournament|clinic|registration|register|sign[- ]?up|free agent|spots|waitlist", re.I)

def relevance(text, kind):
    t = " " + (text or "").lower() + " "
    if not VB.search(t) or NOT_VB.search(t):
        return 0.0, []
    s, why = 2.0, ["volleyball"]
    if ADULT.search(t): s += 1.5; why.append("adult/format cue")
    hits = [p for p in PLACES if p in t]
    if hits: s += min(2.0, 0.8 * len(hits)); why.append("place:" + ",".join(hits[:3]))
    if PROMO_OK.search(t): s += 1.0; why.append("actionable")
    if YOUTH.search(t): s -= 2.5; why.append("youth?")
    if COLLEGE.search(t): s -= 1.0; why.append("college")
    community = kind in ("reclub", "heylo", "meetup_search", "watch", "ics")
    if community: s += 1.5; why.append("community source")
    if not community:
        if OUT_OF_AREA.search(t): s -= 3.0; why.append("out-of-area")
        if not hits: s -= 2.0; why.append("no NorCal place")
    return max(0.0, round(s, 2)), why

def recency(dt, is_event):
    if not dt: return 0.5
    d = (dt - NOW).total_seconds() / 86400
    if is_event:
        if d < -0.2: return 0.0           # already happened
        return max(0.3, 2.0 - d / 7)      # sooner upcoming = higher
    age = -d
    return max(0.0, 2.0 - age / 7)        # newer posts = higher

# ---------------- helpers ----------------
JINA = "https://r.jina.ai/"

def _request(url, timeout=30, accept="*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore"), r.geturl(), getattr(r, "status", 200)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        # raise after attaching body so callers can decide to mirror
        err = e
        err._body = body
        raise

def fetch(url, timeout=30, accept="*/*"):
    """Direct fetch (feeds, Reclub, Meetup, Heylo). Raises on HTTP errors."""
    body, _final, _st = _request(url, timeout, accept)
    return body

def _blocked(status, body):
    if status in (401, 403, 429):
        return True
    if body and "Access Denied" in body[:2000] and len(body) < 5000:
        return True
    return False

def fetch_page(url, timeout=30, accept="*/*", allow_mirror=True):
    """Fetch an official HTML page. If this network is blocked (403/Access Denied),
    retry through the public r.jina.ai reader. Do not use this for RSS/ICS (jina returns markdown)."""
    try:
        body, final, status = _request(url, timeout, accept)
        if allow_mirror and _blocked(status, body):
            raise urllib.error.URLError("blocked status %s" % status)
        return body, {"url": url, "final": final, "status": status, "via": "direct"}
    except Exception as first:
        if not allow_mirror or url.startswith(JINA):
            raise
        last = None
        for attempt in range(2):  # one retry — r.jina.ai occasionally returns 401/422
            try:
                if attempt:
                    time.sleep(1.5)
                body, final, status = _request(JINA + url, timeout=max(timeout, 40), accept="text/plain,*/*")
                if status and int(status) >= 400:
                    raise urllib.error.URLError("jina status %s" % status)
                return body, {"url": url, "final": final, "status": status, "via": "jina"}
            except Exception as e:
                last = e
                continue
        raise last

BLOCKED_CITIES = ["Sunnyvale", "Mountain View", "Menlo Park", "Redwood City", "Walnut Creek", "Folsom", "Emeryville", "Santa Cruz", "Napa"]
# Place aliases and street-name guards so "Folsom Blvd, Rancho Cordova" is not tagged as the city of Folsom,
# and "Redwood Shores" counts for Redwood City coverage.
CITY_ALIAS = [
    (re.compile(r"\bredwood shores\b", re.I), "Redwood City"),
    (re.compile(r"\bredwood city\b", re.I), "Redwood City"),
    (re.compile(r"\bmountain view\b", re.I), "Mountain View"),
    (re.compile(r"\bmenlo park\b", re.I), "Menlo Park"),
    (re.compile(r"\bwalnut creek\b", re.I), "Walnut Creek"),
    (re.compile(r"\bsanta cruz\b", re.I), "Santa Cruz"),
    (re.compile(r"\bsunnyvale\b", re.I), "Sunnyvale"),
    (re.compile(r"\bemeryville\b", re.I), "Emeryville"),
    (re.compile(r"\bnapa\b", re.I), "Napa"),
    # Folsom the city, not Folsom Blvd / Folsom Road in Rancho Cordova or Sacramento
    (re.compile(r"\bfolsom\b(?!\s+(blvd|boulevard|rd|road|ave|avenue|way)\b)", re.I), "Folsom"),
]

def cities_mentioned(*parts):
    t = " " + " ".join(p or "" for p in parts) + " "
    hits = []
    for rx, canonical in CITY_ALIAS:
        if rx.search(t) and canonical not in hits:
            hits.append(canonical)
    return hits

def strip_tags(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s or "", flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def lines(h):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [l.strip() for l in t.split("\n") if l.strip()]

PII = re.compile(r"(venmo|zelle|cash ?app|paypal)\s*[:@-]?\s*\S+|\(?\b\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b", re.I)
def scrub(s): return PII.sub("[removed]", s or "")

def parse_date(s):
    if not s: return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: pass
    for f in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s.replace("Z", "+0000") if "%z" in f else s, f)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except Exception: continue
    return None

def item(source, kind, title, link, dt=None, summary="", is_event=False, extra=None):
    return {"source": source, "kind": kind, "title": scrub(strip_tags(title))[:300], "link": link,
            "date": dt.astimezone(timezone.utc).isoformat() if dt else None,
            "is_event": is_event, "summary": scrub(strip_tags(summary))[:600], **(extra or {})}

# ---------------- collectors ----------------
def from_feed(row):
    name, url = row["name"], row["url"]
    out = []
    body = fetch(url, accept="application/rss+xml,application/atom+xml,text/calendar,application/xml,*/*")
    if "BEGIN:VCALENDAR" in body[:300]:
        for ev in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", body, re.S):
            ev = re.sub(r"\r?\n[ \t]", "", ev)
            g = lambda k: (re.search(rf"^{k}[^:\n]*:(.*)$", ev, re.M) or [None, ""])[1].strip()
            ds = g("DTSTART"); dt = None
            m = re.match(r"(\d{8})(T(\d{6})(Z)?)?", ds)
            if m:
                dt = datetime.strptime(m.group(1) + (m.group(3) or "000000"), "%Y%m%d%H%M%S")
                dt = dt.replace(tzinfo=timezone.utc if m.group(4) else PT)
            out.append(item(name, "ics", g("SUMMARY").replace("\\,", ","), g("URL") or url, dt,
                            (g("LOCATION") + " " + g("DESCRIPTION")).replace("\\n", " ").replace("\\,", ","), True))
        return out
    root = ET.fromstring(body.encode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for it in root.iter("item"):
        t = it.findtext("title") or ""
        out.append(item(name, "rss", t, it.findtext("link") or url, parse_date(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")), it.findtext("description") or ""))
    for e in root.findall(".//a:entry", ns):
        l = e.find("a:link", ns)
        out.append(item(name, "atom", e.findtext("a:title", "", ns), l.get("href") if l is not None else url,
                        parse_date(e.findtext("a:published", "", ns) or e.findtext("a:updated", "", ns)), e.findtext("a:summary", "", ns) or e.findtext("a:content", "", ns) or ""))
    return out

WD = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
def reclub_when(s):
    # "Tue, Nov 10 @ 9:30 PM" or "Friday, January 29, 2027 @ 7:45 PM"
    s = s.replace("\u202f", " ")
    y = datetime.now(PT).year
    for f in ("%a, %b %d @ %I:%M %p", "%A, %b %d @ %I:%M %p", "%A, %B %d, %Y @ %I:%M %p", "%a, %B %d, %Y @ %I:%M %p"):
        try:
            if "%Y" in f:
                d = datetime.strptime(s, f)
            else:
                d = datetime.strptime(f"{y} {s}", "%Y " + f)
                if d.replace(tzinfo=PT) < datetime.now(PT) - timedelta(days=30): d = d.replace(year=y + 1)
            return d.replace(tzinfo=PT)
        except ValueError: continue
    return None

def reclub_meet(mid):
    L = lines(fetch(f"https://reclub.co/m/{mid}"))
    if len(L) < 10: return {}
    i = L.index("English") if "English" in L else 3
    d = {"title": L[i + 1], "when": L[i + 2]}
    for k in range(i + 4, min(i + 24, len(L))):
        if re.search(r", (CA|Ca|ca)\b|United States|California", L[k]) and not re.match(WD, L[k]):
            d["venue"], d["address"] = L[k - 1], L[k]; break
    for k in range(i + 4, min(i + 30, len(L))):
        if re.match(r"^\$[\d.]+$", L[k]) or L[k] in ("Free", "see map Free"):
            d["price"] = (L[k - 1] + " " + L[k]).replace("see map", "").strip(); break
    for l in L:
        if l.startswith("Every "): d["recurrence"] = l; break
    d["labels"] = sorted({l for l in L[i:i + 25] if l in ("Coed", "Adult", "Female", "Male", "Junior", "Senior")})
    return d  # attendee names / payment handles intentionally NOT captured

def from_reclub(club, detail_budget):
    h = fetch(club["url"]); L = lines(h); out = []
    if "Upcoming Activities" not in L: return out
    ids = re.findall(r'href="(?:https://reclub.co)?/m/([A-Za-z0-9]+)"', h)
    k = L.index("Upcoming Activities") + 1; n = 0
    while k < len(L) - 1 and re.match(WD + r", ", L[k]):
        when, title = L[k], L[k + 1]; k += 2
        while k < len(L) and not re.match(WD + r", ", L[k]) and (L[k] == "·" or "Confirmed" in L[k] or "Requested" in L[k] or L[k] == "info"): k += 1
        mid = ids[n] if n < len(ids) else None; n += 1
        dt = reclub_when(when)
        extra = {"club": club["name"], "platform": "Reclub"}
        summary = f"{club['name']} on Reclub. {when}."
        if mid and detail_budget[0] > 0:
            detail_budget[0] -= 1
            try:
                md = reclub_meet(mid)
                if md.get("title") and md["title"] != title: md = {}  # id/order mismatch guard
                extra.update({k2: v for k2, v in md.items() if k2 in ("venue", "address", "price", "recurrence", "labels")})
                summary += " " + " · ".join(str(extra[x]) for x in ("venue", "address", "price", "recurrence") if extra.get(x))
            except Exception: pass
        link = f"https://reclub.co/m/{mid}" if mid else club["url"]
        out.append(item(club["name"], "reclub", title, link, dt, summary, True, extra))
    return out

def from_heylo(g):
    h = fetch(g["url"]); out = []
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m: return out
    seen = set()
    def walk(o):
        if isinstance(o, dict):
            if "deepLink" in o and "/event/" in str(o.get("deepLink")) and "timestamp" in o:
                if o.get("id") in seen: return
                seen.add(o.get("id"))
                dt = datetime.fromtimestamp(o["timestamp"] / 1000, timezone.utc)
                out.append(item(g["name"], "heylo", o.get("name", ""), "https://www.heylo.com" + o["deepLink"].split("?")[0], dt,
                                f"{g['name']} on Heylo. RSVPs: {o.get('rsvpCount', 'n/a')}", True, {"platform": "Heylo"}))
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(json.loads(m.group(1)))
    return out

def from_meetup_search(url):
    h = fetch(url); out = []
    for j in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S):
        try: x = json.loads(j)
        except Exception: continue
        for e in (x if isinstance(x, list) else [x]):
            if e.get("@type") != "Event": continue
            org = (e.get("organizer") or {}).get("name", "")
            loc = (e.get("location") or {}).get("name", "") if isinstance(e.get("location"), dict) else ""
            out.append(item("Meetup: " + org, "meetup_search", e.get("name", ""), e.get("url", url), parse_date(e.get("startDate")),
                            f"{org}. {loc} {e.get('description', '')}", True, {"platform": "Meetup", "club": org}))
    return out

def watch_page(p, state):
    body, meta = fetch_page(p["url"], allow_mirror=True)
    txt = strip_tags(body)
    # hash only text near volleyball mentions so nav/ads churn doesn't trigger
    snip = " | ".join(txt[max(0, m.start() - 250): m.start() + 400] for m in re.finditer(r"(?i)volleyball", txt))[:20000]
    hsh = hashlib.sha256(snip.encode()).hexdigest()
    old = state.get(p["url"])
    state[p["url"]] = {"hash": hsh, "checked": NOW.isoformat(), "snippet": scrub(snip[:400]), "via": meta.get("via"), "http_status": meta.get("status")}
    extra = {"record_id": p.get("record_id"), "fetch_via": meta.get("via"), "http_status": meta.get("status")}
    cities = cities_mentioned(p.get("name", ""), p.get("city", ""), p.get("url", ""), snip)
    if cities:
        extra["cities"] = cities
    if old and old.get("hash") != hsh:
        via = " (via r.jina.ai mirror)" if meta.get("via") == "jina" else ""
        note = "Volleyball-related text on this official page changed since the last run. Re-verify days/times/prices before posting." + via + " New text: " + snip[:400]
        if not snip:
            note = "Official page was fetched" + via + " but no 'volleyball' text was found. If this city used to list a session, treat the listing as unverified until re-checked. " + txt[:300]
        return [item("Page watch", "watch", f"Updated: {p['name']}", p["url"], NOW, note, False, extra)]
    # First successful jina/direct fetch of a blocked official page: emit a coverage lead so Muse sees current schedule text
    if not old and snip and meta.get("via") in ("jina", "direct"):
        # Only emit a 'current listing' lead for blocked-city official pages, not every watch page
        if cities_mentioned(p.get("name", ""), p.get("city", ""), p.get("url", "")):
            via = "Retrieved via r.jina.ai (official site blocks this network)." if meta.get("via") == "jina" else "Retrieved directly."
            return [item("Page watch", "watch", f"Official listing (verify): {p['name']}", p["url"], NOW,
                         via + " Volleyball-related text: " + snip[:400] + " Re-verify days/times/prices before posting.", False, extra)]
    return []

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--days", type=int, default=21, help="keep events up to N days ahead and news up to N days old")
    ap.add_argument("--min-score", type=float, default=3.0)
    ap.add_argument("--max-items", type=int, default=250)
    ap.add_argument("--no-watch", action="store_true")
    ap.add_argument("--feed-url", default="https://example.com/daily_dig.rss", help="public URL where daily_dig.rss will be hosted")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    feeds = list(csv.DictReader(open(os.path.join(HERE, "feeds.csv"))))
    src = json.load(open(os.path.join(HERE, "sources.json")))
    state_p = os.path.join(a.out, "watch_state.json")
    state = json.load(open(state_p)) if os.path.exists(state_p) else {}
    items, log = [], []
    def run(label, fn, *args):
        t = time.time()
        try:
            r = fn(*args); log.append({"source": label, "ok": True, "items": len(r), "secs": round(time.time() - t, 1)}); return r
        except Exception as e:
            log.append({"source": label, "ok": False, "error": f"{type(e).__name__}: {str(e)[:120]}"}); return []
    budget = [int(src.get("reclub_meet_detail_limit", 60))]
    with cf.ThreadPoolExecutor(10) as ex:
        futs = [ex.submit(run, f["name"], from_feed, f) for f in feeds]
        futs += [ex.submit(run, "Heylo: " + g["name"], from_heylo, g) for g in src.get("heylo_groups", [])]
        futs += [ex.submit(run, "Meetup search: " + u.split("--ca--")[-1], from_meetup_search, u) for u in src.get("meetup_search_pages", [])]
        for f in futs: items += f.result()
    with cf.ThreadPoolExecutor(4) as ex:  # Reclub politely, fewer threads
        for r in ex.map(lambda c: run("Reclub: " + (c.get("name") or c["slug"]), from_reclub, c, budget), src.get("reclub_clubs", [])): items += r
    if not a.no_watch:
        with cf.ThreadPoolExecutor(8) as ex:
            for r in ex.map(lambda p: run("Watch: " + p["name"][:50], watch_page, p, state), src.get("watch_pages", [])): items += r
        json.dump(state, open(state_p, "w"), indent=1)
    # score + filter
    kept, seen = [], set()
    horizon_f, horizon_p = NOW + timedelta(days=a.days), NOW - timedelta(days=a.days)
    for it in items:
        dt = datetime.fromisoformat(it["date"]) if it["date"] else None
        if dt and it["is_event"] and not (NOW - timedelta(hours=5) <= dt <= horizon_f): continue
        if dt and not it["is_event"] and dt < horizon_p: continue
        community = it["kind"] in ("reclub", "heylo", "meetup_search", "watch", "ics") or it["source"].startswith("Meetup")
        rel, why = relevance(it["title"] + " " + it["summary"] + (" " + it["source"] if community else ""), "ics" if community and it["kind"] in ("rss", "atom") else it["kind"])
        if rel < a.min_score: continue
        key = re.sub(r"[^a-z0-9]", "", it["title"].lower())[:60] + "|" + (it["date"] or "")[:13]
        if key in seen: continue
        seen.add(key)
        it["relevance"], it["why"] = rel, why
        it["recency"] = round(recency(dt, it["is_event"]), 2)
        it["score"] = round(rel + it["recency"], 2)
        it["date_local"] = dt.astimezone(PT).strftime("%a %b %d %Y, %I:%M %p PT") if dt else None
        it["verification_state"] = "DISCOVERED"  # per Ask Diggy schema: verify before publishing
        cites = it.get("cities") or cities_mentioned(it["title"], it["summary"], it.get("venue"), it.get("address"), it["source"], it.get("club"), it.get("link"))
        if cites:
            it["cities"] = cites
        kept.append(it)
    kept.sort(key=lambda x: (-x["score"], x["date"] or ""))
    kept = kept[: a.max_items]
    events = sorted([k for k in kept if k["is_event"]], key=lambda x: x["date"] or "")
    news = [k for k in kept if not k["is_event"]]
    # Per blocked-city coverage (Sunnyvale, Mountain View, Menlo Park, Redwood City, Walnut Creek, Folsom, Emeryville, Santa Cruz, Napa)
    blocked_report = {}
    for city in BLOCKED_CITIES:
        ev = [k for k in events if city in (k.get("cities") or [])]
        nw = [k for k in news if city in (k.get("cities") or [])]
        src_hits = [l for l in log if city.lower() in (l.get("source") or "").lower()]
        blocked_report[city] = {
            "events": len(ev),
            "news_and_updates": len(nw),
            "sample_events": [{"date_local": e.get("date_local"), "title": e["title"], "source": e["source"], "link": e["link"], "verification_state": e.get("verification_state")} for e in ev[:8]],
            "sample_news": [{"title": n["title"], "source": n["source"], "link": n["link"]} for n in nw[:5]],
            "sources_ok": sum(1 for l in src_hits if l["ok"]),
            "sources_failed": sum(1 for l in src_hits if not l["ok"]),
        }
    meta = {"generated_at": NOW.isoformat(), "generated_at_local": NOW.astimezone(PT).strftime("%Y-%m-%d %I:%M %p PT"),
            "counts": {"raw_items": len(items), "kept": len(kept), "events": len(events), "news_and_updates": len(news)},
            "sources_ok": sum(1 for l in log if l["ok"]), "sources_failed": sum(1 for l in log if not l["ok"]),
            "blocked_cities": blocked_report,
            "rules": "All items are DISCOVERED leads. Verify with the organizer source before posting. Never infer missing facts."}
    json.dump({"meta": meta, "events": events, "news_and_updates": news, "source_log": log, "blocked_cities": blocked_report}, open(os.path.join(a.out, "daily_dig.json"), "w"), indent=1, ensure_ascii=False)
    # RSS
    rss = ET.Element("rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = "The Daily Dig – NorCal & Bay Area adult volleyball"
    ET.SubElement(ch, "link").text = a.feed_url
    ET.SubElement(ch, "description").text = "Merged, filtered feed of adult volleyball open gyms, pickups, leagues, tournaments and news across Northern California. Leads only – verify with organizers."
    ET.SubElement(ch, "lastBuildDate").text = format_datetime(NOW)
    ET.SubElement(ch, "{http://www.w3.org/2005/Atom}link", href=a.feed_url, rel="self", type="application/rss+xml")
    for it in events + news:
        e = ET.SubElement(ch, "item")
        pre = f"[{it['date_local']}] " if it["is_event"] and it.get("date_local") else ""
        ET.SubElement(e, "title").text = pre + it["title"]
        ET.SubElement(e, "link").text = it["link"]
        ET.SubElement(e, "guid", isPermaLink="false").text = hashlib.sha1((it["link"] + (it["date"] or "") + it["title"]).encode()).hexdigest()
        ET.SubElement(e, "category").text = it["kind"]
        ET.SubElement(e, "source", url=it["link"]).text = it["source"]
        ET.SubElement(e, "description").text = f"{it['summary']} (score {it['score']}; {', '.join(it['why'])}; status DISCOVERED – verify before posting)"
        ET.SubElement(e, "pubDate").text = format_datetime(datetime.fromisoformat(it["date"]) if it["date"] and not it["is_event"] else NOW)
    ET.ElementTree(rss).write(os.path.join(a.out, "daily_dig.rss"), encoding="utf-8", xml_declaration=True)
    # Markdown
    md = [f"# The Daily Dig – {meta['generated_at_local']}", "",
          f"{len(events)} upcoming sessions/events and {len(news)} news/updates (from {meta['sources_ok']} sources; {meta['sources_failed']} failed).",
          "All items are **leads (DISCOVERED)**. Confirm on the linked organizer page before posting.", "", "## Upcoming (next %d days)" % a.days, ""]
    day = None
    for it in events:
        d = datetime.fromisoformat(it["date"]).astimezone(PT).strftime("%A, %b %d") if it["date"] else "Date unknown"
        if d != day: md += ["", f"### {d}"]; day = d
        t = datetime.fromisoformat(it["date"]).astimezone(PT).strftime("%I:%M %p").lstrip("0") if it["date"] else ""
        bits = " · ".join(x for x in [it.get("venue"), it.get("price"), it.get("club") or it["source"]] if x)
        md.append(f"- **{t}** [{it['title']}]({it['link']}) — {bits}")
    md += ["", "## News & page updates", ""]
    for it in news[:60]:
        md.append(f"- [{it['title']}]({it['link']}) — {it['source']}" + (f" ({it['date_local']})" if it.get("date_local") else ""))
    md += ["", "## Blocked-city coverage", "", "These cities have official pages that often return 403 to cloud servers. The script retries those pages through r.jina.ai and also reads Meetup, Reclub, Heylo and per-city news feeds. Counts are items kept after filtering. All are DISCOVERED leads.", ""]
    for city, rep in blocked_report.items():
        md.append(f"- **{city}**: {rep['events']} upcoming events, {rep['news_and_updates']} news/updates.")
        for e in rep["sample_events"][:3]:
            md.append(f"  - {e.get('date_local') or ''} [{e['title']}]({e['link']}) — {e['source']}")
        if rep["events"] == 0 and rep["news_and_updates"] == 0:
            md.append("  - No kept items this run. See blocked_cities.md for fallbacks still in place.")
    md += ["", "## Source health", ""] + [f"- {'OK' if l['ok'] else 'FAIL'} {l['source']}" + (f" ({l.get('items')} items)" if l["ok"] else f" — {l.get('error')}") for l in log]
    open(os.path.join(a.out, "daily_dig.md"), "w").write("\n".join(md) + "\n")
    # compact blocked-city report for the operator
    print(json.dumps({"meta_counts": meta["counts"], "sources_ok": meta["sources_ok"], "sources_failed": meta["sources_failed"],
                      "blocked_cities": {c: {"events": blocked_report[c]["events"], "news": blocked_report[c]["news_and_updates"], "sources_ok": blocked_report[c]["sources_ok"], "sources_failed": blocked_report[c]["sources_failed"]} for c in blocked_report}}, indent=1))

if __name__ == "__main__":
    main()
