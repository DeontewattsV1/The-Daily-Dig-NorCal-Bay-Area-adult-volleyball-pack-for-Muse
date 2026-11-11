# The Daily Dig: NorCal & Bay Area adult volleyball pack for Muse

Built 2026-11-10 (PT) for @ask.diggy. Everything here is public-web data with a source link and a verification date. **Nothing has been posted, and no accounts were signed into.**

## What's in the folder
| File | What it is | How Muse should use it |
|---|---|---|
| `open_gyms.csv` / `open_gyms.json` | **112 programs** across **51 named cities** and 15 counties: city drop-ins, private gyms and clubs, Reclub/Heylo/Meetup groups, leagues, tournament organizers, public beach and grass courts. Fields: name, org type, city, county, venue, address, format, level, days/times, price, platform, booking URL, socials, contact, source URL, HTTP status, last verified, how verified, status, notes, old directory ID. | **Long-term knowledge base.** Answer "where can I play…?" from it. Always link `booking_url`/`source_url` and say "last checked {last_verified}". Treat `unknown` as unknown, never as "no". |
| `platforms.md` | Platform-by-platform guide (Reclub, Heylo, Meetup, city systems, LeagueApps, Volo, GoodRec, VolleyballLife, Instagram, Facebook, Reddit, YouTube…), including which have RSS/API/ICS, how to monitor each, and Terms of Service limits. | Read once. Use it to decide where to look when a user asks about a specific org. |
| `feeds.csv` / `feeds.opml` | Working feeds (Google News including **per-blocked-city queries**, Meetup RSS/ICS, volleyball and local paper news, city CivicPlus feeds), each checked with an HTTP request. Meetup feeds with 0 items are valid but have no upcoming events right now. | Import the OPML into any feed reader, or let `daily_dig.py` read the CSV. |
| `feeds_failed.csv` | Candidate feeds that didn't work from this server (Reddit 429/403, YouTube intermittent 404, some city CivicPlus RSS 403, some Meetup group RSS “Invalid feed signature”, Bing News empty, Patch 404). | Retry from a home network, a GitHub Actions runner, or via official APIs. |
| `sources.json` | Scrape/watch list: Reclub clubs, Heylo groups, Meetup city searches (including blocked cities), official program pages to watch, plus a `blocked_cities` block. | Edit to add or remove sources. |
| `daily_dig.py` | Aggregator (Python 3.9+, **standard library only**). Pulls feeds, scrapes Reclub, Heylo and Meetup, watches official pages for changes, **retries 403 city pages through r.jina.ai**, filters for adult NorCal volleyball, removes duplicates, scores relevance + recency, and strips personal data. | Run daily. |
| `blocked_cities.md` | Per-city fallback map for Sunnyvale, Mountain View, Menlo Park, Redwood City, Walnut Creek, Folsom, Emeryville, Santa Cruz and Napa: what works from this network, what still needs a home connection or GitHub Actions. | Read when a city official page is blocked or a slot looks stale. |
| `handles.csv` | Curated Instagram handles for organizers, venues, city rec accounts and the posting account. `tag_ok=yes` only when the handle was confirmed on a public page (or explicitly marked IG VERIFIED in the owner directory). Everything else is **do-not-tag**. | Only @-tag rows with `tag_ok=yes`. Never tag players or private people. |
| `MUSE_POST_PROMPT.md` | Ready-to-paste system/task prompt for turning `daily_dig` output into Instagram posts, stories and carousels for **@ask.diggy**, including caption templates, hashtags, the @-tag policy and example posts. | Paste into Muse. Human approval is required before anything goes live. |
| `.github/workflows/daily-dig.yml` | GitHub Actions template that runs the aggregator on a schedule from GitHub's network (often not blocked by city sites). **Documented, not deployed.** | Copy into a repo only if Deonte asks to host the feed. |
| `out/daily_dig.json`, `out/daily_dig.rss`, `out/daily_dig.md` | Output of the latest run, including a `blocked_cities` coverage report. | Muse digests `daily_dig.json` (or subscribes to the RSS) each morning. |
| `ICLOUD_SOURCE_REVIEW.md` | What was in the iCloud folder and how it was used. | Context. |

## How to run
```bash
python3 daily_dig.py                       # full run (~1 min), writes out/
python3 daily_dig.py --days 14 --min-score 3.5
python3 daily_dig.py --no-watch            # skip official-page change checks
python3 daily_dig.py --feed-url https://<your-host>/daily_dig.rss
```
On the first run, page-watch just records a baseline. From the second run on, any change to a program page's volleyball text shows up as an "Updated: …" item, which means **re-verify that program**.

## Daily routine for Muse
1. **7:00 AM PT:** run `daily_dig.py` (or read the hosted `daily_dig.rss`).
2. Read `out/daily_dig.json` → `events` (sorted by time) and `news_and_updates`.
3. For each item you might post: open the `link`, confirm the date, time, venue, price and 18+ eligibility on the organizer's page, then mark it VERIFIED (per the Ask Diggy schema). Items arrive as `DISCOVERED`.
4. Look at the `Updated:` items. A city page changed, so recheck the matching `open_gyms.csv` row (`record_id`) and update `days_times`, `price` and `last_verified`.
5. Weekly (Sunday): skim `source_log` in the JSON for failed sources. Quarterly (city seasons change around Jan, Apr, Jun and Sep): re-verify every `city` row.

**Refresh cadence:** Reclub, Heylo and Meetup change daily, so run once a day. City pages change by season, so the watch check is enough. Feeds change hourly, so once a day is plenty for an Instagram account.

## Instagram posts and @-tags
Use **`MUSE_POST_PROMPT.md`** as the ready-to-paste brief. Only @-tag handles with `tag_ok=yes` in `handles.csv`. Never tag individual players or private people. Every draft needs a human check before it goes live on @ask.diggy.

## Instagram content ideas (draft for approval; never auto-post)
- **"Tonight's Dig"** story each weekday: 3–5 sessions from `events` for that evening, with time, venue, level, price and the organizer handle. Example: "7:00 pm BSH coed B/BB @ Urban Promise Academy, Oakland, $15 (Reclub)".
- **Weekend planner** carousel (Thu/Fri): grass, beach and indoor options by region (SF/Peninsula, East Bay, South Bay, Sacramento, North Bay).
- **Free & cheap gyms** reel: SF Rec & Park free drop-ins, Menlo Park $2–3, Mountain View $3, Benicia $4.25, Berkeley/Antioch/HARD $5. Re-verify before posting.
- **Level guide** (B / BB / A / AA / Open; what "reverse coed" means), linking to sessions labelled with each level.
- **Women's volleyball spotlight**: SF Women's Volleyball (Reclub), SF Rec & Park women's drop-ins, VWPG Women's.
- **Beginner corner**: SFBV beginner socials, SF Dynasty and SVVC beginner/intermediate clinics, MVVC clinics.
- **Organizer of the week**: credit and tag the organizer, and link their Reclub/Meetup/Heylo page. Get permission before using their photos.
- **"Where do I play in ___?" replies**: answer from `open_gyms.csv`, filtered by city/county, and include "last checked" plus the link.
- Always include the AI-assistance disclosure and organizer credit (Daily Dig system cards). Never share attendee names or payment handles.

## Hosting the merged feed (optional; not deployed)
- **GitHub Actions + GitHub Pages:** a ready-to-copy workflow is in `.github/workflows/daily-dig.yml`. It is a template only and has not been enabled. Put this folder in a repo, replace the `--feed-url` placeholder, and (optionally) serve `out/` with Pages. GitHub runners use a different IP range and may fetch official city pages directly; the script also falls back to r.jina.ai when a page is blocked. See `blocked_cities.md`.
- **Vercel:** serve `out/` as static files and regenerate with a Vercel Cron job or a GitHub Action that redeploys.
- Keep the repo **private** if it holds anything from the confidential Muse pack. This folder itself holds only public data.

## Accuracy rules (from the Ask Diggy operating pack)
- Never invent dates, prices, levels or eligibility. `unknown` means not confirmed.
- `verify_method` explains how each row was checked: `official_page_fetched` (read directly), `official_page_search_indexed` (the city site blocks servers, so the text was read from the search index today), `platform_page_fetched` (live Reclub/Heylo/Meetup), or `owner_directory_2026-11-01` (carried over, not re-checked).
- `status`: active, dormant (no upcoming sessions listed), irregular, informal (public courts), stale_needs_recheck, or unverified_current.
- Several rows are 14+/16+ rather than 18+ (San Jose Camden 14+, Napa 16+, Roseville 16+, Basketball Nation 16+), and the Mark Green session is tagged "Junior" on Reclub. Say so when promoting them.
