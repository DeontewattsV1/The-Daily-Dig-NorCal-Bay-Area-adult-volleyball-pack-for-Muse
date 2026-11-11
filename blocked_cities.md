# Blocked-city fallbacks for the Daily Dig

Checked **2026-11-10 (America/Los_Angeles)**. Several city parks-and-rec sites return **403 Access Denied** to this cloud network (Akamai/bot filter). Muse still needs to know what’s happening with adult volleyball in those cities. This note is the coverage map. Nothing here was posted, and no accounts were signed into.

**The working fallback used in `daily_dig.py`:** when an official program page returns 403/401/“Access Denied”, the script retries it through the public reader `https://r.jina.ai/<url>`. That reader returned HTTP 200 and usable volleyball text for every blocked official page tested today, except Folsom (the Folsom pages loaded but did **not** list a volleyball drop-in — see below).

**Also wired in:** per-city Google News RSS (validated with curl; mostly high-school noise, filtered by the aggregator), Meetup search pages and working Meetup RSS/ICS, Reclub community pages already in `sources.json`, nearby private-gym feeds (Reclub/Heylo), local paper RSS where it actually worked, city catalog pages that load directly (Menlo Park PerfectMind, Napa Adult Sports), and a **documented, not deployed** GitHub Actions workflow (`.github/workflows/daily-dig.yml`) that runs the same script from GitHub’s network.

**What still needs a home network or a GitHub Actions runner:** a first-party copy of the blocked official HTML (jina is a third-party reader), CivicPlus news/calendar RSS for Folsom and Emeryville (403 direct; jina did not return a usable feed), several Meetup group RSS/ICS URLs that now return “Invalid feed signature” (events still show up via Meetup search), Reddit search RSS (429/403), and YouTube channel RSS (flaky). Bing News RSS and Patch city RSS were tested and are **not useful** from this network (0 items or 404).

All items the script emits are **DISCOVERED leads**. Verify days, times, prices and 18+ eligibility on the organizer’s page before posting. Never invent a session that the official page no longer lists.

---

## How Muse should use this

1. Run `python3 daily_dig.py` as usual. Official blocked pages are retried via r.jina.ai automatically. Per-city counts land in `out/daily_dig.json` → `blocked_cities` and in the “Blocked-city coverage” section of `out/daily_dig.md`.
2. Prefer live Reclub / Meetup / Heylo sessions (they come with a date) over a city schedule snippet.
3. Treat a city schedule from jina as a **lead**: quote it, link the official URL (not the jina URL) and re-verify before posting.
4. If you can run the script at home or via the GitHub Action, do that for a first-party fetch. The workflow file is a template only; it has not been deployed.

---

## Sunnyvale

| Path | Status today |
|---|---|
| Official drop-in gym page (`sunnyvale.ca.gov/.../drop-in-gym`) | Direct **403**. **r.jina.ai 200.** Volleyball, 18 and up, **Tue 5–7 pm** at the Sunnyvale Indoor Sports Center. Closures/holiday language is on the page. Pass prices were last seen via the search index on 2026-11-10 and were not restated in the jina snippet — re-check price before posting. |
| Per-city Google News RSS | **200**, 10 items, mostly high school. Filter applies. |
| Meetup | Search `meetup.com/find/us--ca--sunnyvale/volleyball/` **200** with JSON-LD events. Working group feeds: Sunnyvale Grass Volleyball and Sunnyvale Rec Volleyball (RSS + ICS). Sunnyvale / San Jose Volleyball (`volleyball-group`) and Lunch Time VB RSS returned **403 Invalid feed signature** — events still appear via Meetup search. |
| Reclub community | `reclub.co/communities/us/california/sunnyvale` **200**. Clubs include MVVC (in Sunnyvale), Bay Area Grass Meetups (Las Palmas Park), VWPG Women’s, ~BB+ Doubles. |
| Nearby private / already-watched | MVVC late-night sessions, Saturday grass at Las Palmas Park. |
| Local news | Mountain View Voice / Palo Alto Online / Almanac general feeds are in `feeds.csv` (filter for volleyball). |
| Still needs home / GitHub | Raw official HTML; Lunch Time and volleyball-group Meetup RSS/ICS; Reddit. |

## Mountain View

| Path | Status today |
|---|---|
| Official adult sports page | Direct **403**. **r.jina.ai 200.** Adult drop-in volleyball **Sundays 5:00–7:30 pm** at Mountain View Sports Pavilion, 1185 Castro St. For **Mountain View residents and employees of Mountain View businesses**. Day pass **$3**; **$15 / 10 visits**, **$30 / 20 visits**. A 2025 holiday closure listed on the page is already in the past; no 2026 closure was in the text retrieved today. |
| Per-city Google News RSS | **200**, 27 items, very noisy (including out-of-state “Mountain View” high schools). Filter applies; still watch for false positives. |
| Meetup | Search `meetup.com/find/us--ca--mountain-view/volleyball/` **200** with JSON-LD events. |
| Reclub community | **200**. Clubs include SVVC and ~BB+ Doubles (the Google 2000 sand-court listing may be a private campus — do not promote venue access). |
| Nearby private / already-watched | SVVC Sunday clinic in Mountain View; MVVC is physically in Sunnyvale. |
| Local news | Mountain View Voice feed added. |
| Still needs home / GitHub | Raw official HTML; Reddit. |

## Menlo Park

| Path | Status today |
|---|---|
| Official volleyball page | Direct **403**. **r.jina.ai 200.** **Drop-in volleyball (18+)** at Arrillaga Family Gymnasium. Weekdays **$2**; Sunday **6:30–9:30 pm $3**. The page lists **Mon 8–10 am and 5–8 pm**, **Wed 8 am–1 pm**. A **youth** drop-in (Mon/Wed 3–5 pm) and youth leagues are on the same page — **do not promote** them. |
| PerfectMind booking calendar | **Direct 200** (this one is not blocked). Watched as of this pack. Class rows may be JavaScript-rendered; use it as a live catalog when the HTML shows “Drop-in Volleyball”. |
| Per-city Google News RSS | **200**, 9 items, noisy. |
| Meetup | Path-style `/find/us--ca--menlo-park/volleyball/` was **404**. Query-style `meetup.com/find/?keywords=volleyball&location=us--ca--menlo-park` was **200** with JSON-LD events and is in `sources.json`. MP Volleyball group RSS still works (0 upcoming items today). |
| Reclub community | **200**, only Bay Area Open Gyms listed. |
| Local news | The Almanac and InMenlo feeds added. |
| Still needs home / GitHub | Raw official HTML; fuller PerfectMind slot times if they only appear after JavaScript. |

## Redwood City

| Path | Status today |
|---|---|
| Official open-gym page and calendar event | Direct **403**. **r.jina.ai 200.** The open-gym page confirms the Armory and Red Morton gyms host drop-in volleyball (among other sports) and lists adult open-gym rates. Exact volleyball slot times were not cleanly extracted today — check the official schedule before posting. Prior directory price: adults $5 (re-verify). |
| City calendar RSS | **Already working** (`feeds.csv`, direct 200) — no mirror needed. |
| Per-city Google News RSS | **200**, 10 items, noisy. |
| Meetup | Path-style find URL **404**. Query-style `location=us--ca--redwood-city` **200** with events, now in `sources.json`. Redwood Shores/City Grass group RSS/ICS returned **403 Invalid feed signature**; events still appear via Meetup search (e.g. Friday intermediate/advanced grass). |
| Reclub community | **200**, club sample included Matcha (verify any Meet against the actual venue before posting). |
| Nearby private / already-watched | SportsHouse Redwood City (`sportshouse.us`) **direct 200**, already in the watch list and directory. |
| Local news | Almanac and Palo Alto Online feeds. |
| Still needs home / GitHub | Raw official HTML and a clear slot-time table; Redwood Shores Meetup RSS/ICS. |

## Walnut Creek

| Path | Status today |
|---|---|
| Official drop-in sports page (Tice Valley Gym) | Direct **403**. **r.jina.ai 200.** Fall schedule **effective 8/10/26**: **Monday–Friday 12–3 pm**, volleyball & basketball shared, at Tice Valley Gym, 2055 Tice Valley Blvd. **$8** per session or **$70** 10-visit pass (debit/credit only, no cash). Closures listed: **11/11, 11/25–11/27, 12/24–1/01** (dates subject to change). The older directory row that said “Fri 12–3 pm only” is superseded by this official text; re-verify before posting. |
| Per-city Google News RSS | **200**, 10 items, noisy. |
| Meetup | `meetup.com/find/us--ca--walnut-creek/volleyball/` and beach search were already in `sources.json`. |
| Reclub / Heylo | Community page **200** (Bay Area Open Gyms, BSH). SF Pickup Volleyball (Heylo) already lists a recurring “Walnut Creek CO ED Volleyball High Intermediate” session — a live dated source. 24 Hour Fitness Walnut Creek Sunday open gym is on Reclub (gym access likely required). |
| Local news | No Walnut Creek-specific paper RSS was validated today. East Bay Times search-RSS was HTML, not a feed. |
| Still needs home / GitHub | Raw official HTML; a local paper feed if you find a working one. |

## Folsom

| Path | Status today |
|---|---|
| Official Adult Sports page and `/sports/volleyball` URL | Direct **403**. **r.jina.ai 200, but no volleyball drop-in is listed in the page text today.** Treat the prior search-indexed listing (Sun 2:30–5:30 pm, $7, Folsom Middle School Gym) as **unverified / possibly stale**. **Do not post that slot** until a home-network fetch, a GitHub Actions run, or a new official/Meetup source confirms it. Directory status is `stale_needs_recheck`. |
| CivicPlus news/calendar RSS | Direct **403**. r.jina.ai returned **422** / not a usable feed. **Needs home or GitHub.** |
| Per-city Google News RSS | **200**, 19 items, noisy. |
| Meetup | Path-style find URL **404**. Query-style `location=us--ca--folsom` **200** with events, now in `sources.json`. Folsom Intermediate Sand Volleyball group RSS/ICS returned **403 Invalid feed signature**; events still appear via Meetup search (e.g. Thursday night, Monday night intermediate quads). |
| Reclub community | **200**, SkillSet Sacramento listed. |
| Nearby / already-watched | Adult Volleyball Program (Sacramento) Meetup ICS already in `feeds.csv` (some listings mention Folsom — confirm the venue, don’t assume). |
| City Instagram | **None found** on the official homepage today. Do not guess a handle (see `handles.csv`). |
| Local news | Folsom Telegraph `/feed` and `/rss.xml` were HTML, not RSS. Not added. |
| Still needs home / GitHub | First-party official HTML (to confirm whether the city drop-in still exists); CivicPlus RSS; Folsom Intermediate Meetup RSS/ICS; a local paper feed. **This is the thinnest official-city coverage in the set.** |

## Emeryville

| Path | Status today |
|---|---|
| Official Open Gym Volleyball page | Direct **403**. **r.jina.ai 200.** Sundays **2:00–7:00 pm**, **ages 18+**, all skill levels, at the Emeryville Center of Community Life. Adult (18–49) drop-in **$6 resident / $7 non-resident**; 10-visit **$49R / $55NR**. Official city Instagram **@cityofemeryville** is listed on the page (tag-ok in `handles.csv`). |
| CivicPlus news/calendar RSS | Direct **403**. jina returned a “Page Not Found” document. **Needs home or GitHub.** |
| Per-city Google News RSS | **200**, 3 items, mostly high school / general rec. |
| Meetup | `meetup.com/find/us--ca--emeryville/volleyball/` **200** with JSON-LD events. |
| Reclub community | **200**, 0 clubs listed today. |
| Local news | The E’ville Eye feed added (general neighborhood news; filter applies). |
| Still needs home / GitHub | Raw official HTML; CivicPlus RSS. |

## Santa Cruz

| Path | Status today |
|---|---|
| Official City Beaches page | Direct **403**. **r.jina.ai 200.** **18 beach volleyball courts** at Main Beach, first come first served, reservations encouraged, professional-grade nets, men’s and women’s heights. Informal pickup is not a city-run session. A beginner group “Tue ~5:30 pm near court 15” is a **community report** — label it unverified. |
| Per-city / existing Google News | A Santa Cruz beach-volleyball Google News feed was already in `feeds.csv` (**200**, 45 items, often high school or college). Filter applies. |
| Meetup | Path-style find URL **404**. Query-style `location=us--ca--santa-cruz` **200** with events, now in `sources.json`. Livermore Pickup Beach Volleyball (already in feeds) sometimes runs Santa Cruz meetups — confirm the venue. |
| Reclub community | **200**, 0 clubs. |
| Nearby / already-watched | CBVA (`cbva.com`, official IG **@thecbva**) already in the directory. |
| Local news | Santa Cruz Sentinel site and search-RSS were 403 / not XML from this network. **Needs home or GitHub.** |
| Still needs home / GitHub | Raw official HTML; Sentinel feed; Reddit r/santacruz. |

## Napa

| Path | Status today |
|---|---|
| Official Adult Sports page | **Direct 200 today** (it returned 500 on an earlier pass). **No mirror needed right now.** Adult drop-in volleyball, Harvest Recreation Complex (small gym), **Sundays 3:30–5:30 pm**, **$7** per Sunday/evening session, 10-visit pass **$63**. The page lists this under Adult Drop-In Sports and does **not** restate a 16+ floor on the volleyball line (the prior directory said 16+ waiver; basketball on the same page is 16+ only). **Verify age eligibility before posting.** |
| Rec1 catalog (`secure.rec1.com/CA/napa-ca/catalog`) | Direct **200**, but the HTML had **no volleyball text** (likely JavaScript-rendered). Not a reliable scraper source from this script. |
| City news-flash RSS | **Already working** in `feeds.csv` (0 items at last check). |
| Per-city Google News RSS | **200**, 11 items, noisy. |
| Meetup | Path-style find URL **404**. Query-style `location=us--ca--napa` **200** with events, now in `sources.json`. |
| Reclub community | **404**. |
| Local news | Napa Valley Register search-RSS returned only old items (2011–2024). Not added. |
| Still needs home / GitHub | A Rec1 catalog that exposes volleyball rows without JavaScript; a current local paper feed. Official city page itself is fine from this network today. |

---

## Fallbacks that were tested and are not used

- **Bing News RSS** (`bing.com/news/search?...&format=rss`): HTTP 200, **0 items** for every blocked city. Documented in `feeds_failed.csv`.
- **Patch** city `/rss` paths: **404**. `patch.com/feeds/california/sunnyvale` was 200 with 0 items.
- **Google webcache**: returned a Google Search shell, not a cached page.
- **DuckDuckGo HTML search**: 200, but it is a search page, not a feed, and is not scraped (fragile, no structured events).
- **Folsom Telegraph** `/feed` and `/rss.xml`: HTML, not RSS.
- **CivicPlus RSS via r.jina.ai** for Folsom/Emeryville: 422 or a not-found page.

If you later find a working first-party ICS or catalog endpoint (ActiveNet, CivicRec, PerfectMind, Rec1, MyRec) for a blocked city, add the URL to `feeds.csv` (if it is RSS/ICS) or `sources.json` → `watch_pages` (if it is HTML) and re-run. PerfectMind for Menlo Park and the Napa Adult Sports page are the two catalogs that already work directly.
