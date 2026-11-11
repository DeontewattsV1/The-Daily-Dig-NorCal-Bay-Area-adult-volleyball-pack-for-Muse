# What was in the iCloud folder, and how it was used

Share: https://www.icloud.com/iclouddrive/01fqpnmBkyuNkevWQQmJuvuJg (public, read anonymously on 2026-11-10)
The root item is a folder named `new_database.db`: 51 files, about 4.5 MB, plus a `Skills/` subfolder. Everything was downloaded to the box at `/workspace/volleyball/source/` and is **not** copied into this pack (to keep it small and to avoid moving confidential files around).

## Contents (grouped)
| Group | Files | Used how |
|---|---|---|
| **Existing organizer directory** | `NorCal_Adult_Volleyball_Master_Directory.csv` / `.xlsx` (×3 identical, 151 rows, 25 marked verified 2026-11-01) | Baseline. Every new row in `open_gyms.csv` that matches an old row carries its `owner_directory_id` (VB-xxx). The 45 youth clubs marked "adult program UNVERIFIED" were left out (adult scope). Several entries were upgraded with live venue, day, time and price data from Reclub. |
| **Organizer lists (md/pdf)** | "Complete List of Northern California/Bay Area Adult Volleyball Organizers – Official & Unofficial", "Northern California/Bay Area Volleyball Organizations – Complete List / Alphabetical", "Northern California Volleyball Organizations Contact & Logo Resources", "NorCal volleyball.pdf" | Cross-checked for names only. They are older AI-assisted lists, so nothing from them was published without a fresh source. |
| **Research pack** | `norcal_volley_intel_research_pack_2026-08-13.zip` (tournament calendar Aug–Sep 2026, organizer contacts, verification report, Daily Dig publication schedule) | Used for organizer contacts (CBVA, VolleyNation, TLS, BSH) and its scoring rubric idea. Its events are past, so it's historical only. |
| **Muse operating pack** | `ASK_DIGGY_MUSE_OPERATING_PACK_V1_1.zip` (memory, operating rules, canonical event schema, reply library, connector matrix) | **Format contract.** The public account is **@ask.diggy**. Everything new is a lead labelled `DISCOVERED` and must be verified before publishing. Field names follow `04_CANONICAL_EVENT_SCHEMA.json` where possible. Privacy rules (no player data) are built into `daily_dig.py`. |
| **Daily Dig system** | `daily dig system cards.md`, `daily dig deployment prompt.md`, `DAILY_DIG_CONTENT_INTELLIGENCE_V2.zip` (FastAPI/Postgres content-intelligence service), `001/002 *.sql`, `openapi.json`, `production readiness checklist.md`, `BSH VB Infrastructure Deployment.md`, `system cards deployment.pdf` | Matched the scope (18+, NorCal, verify with 2 sources, organizer credit). `daily_dig.json` can be loaded into that service's `events` pipeline later. |
| **Instagram AI memory blocks** | "Instagram AI Database – Volleyball Memory Block 1–4", "BSH VB Instagram AI Bot System Prompt", "Strategic Implementation and Configuration of Inst….pdf", "Claude Behavior Guidelines for Volleyball Tournament Chats" | Voice and tone reference only. Not re-published. |
| **Tournament list** | "Northern California Adult Volleyball Tournaments – Open for Registration (Jan 31 – Apr 2026)" | Past, so historical. |
| **Other** | `Skills/` (agent_configuration, architecture, built_in_tools, local_models, mcp_integration, observability), `secrets and governance code.py`, `text*.txt`, images (system architecture, NotebookLM mind map) | Not needed for this task. `secrets and governance code.py` was **not opened or copied**. |

## Notes
- The Reclub club called **"Matcha"** (257 members; Fri Nov 13 BB/A/AA men's open gym at SF Elite VBC, South SF) has the same name as Deonte's Matcha project. Confirm whether it's his before treating it as a third party.
- The old directory listed Xoso's domain as `xosososports.com`. The working site is `xososports.com`.
- The old directory's NCVA note (adult league **suspended 2026–27**) was kept as-is (not re-checked today).
