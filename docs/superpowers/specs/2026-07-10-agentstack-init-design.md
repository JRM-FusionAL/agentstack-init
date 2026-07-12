# agentstack-init — Design Spec

**Status**: Approved (rev 2, 2026-07-10)
**Date**: 2026-07-10  
**Author**: Jonathan Melton / Claude Code (brainstorming session)  
**Skill**: superpowers:brainstorming → writing-plans

---

## Overview

`agentstack-init` is an open-source MCP server + CLI scaffolder targeting developers whose AI harness configs are broken — MCP servers silently failing, CLAUDE.md ignored, no cross-session memory. It is a **lead magnet**, not a product. Revenue comes from the consulting funnel it feeds.

```
Free tool users ──→ Email capture / audit report ──→ Audit call ──→ $750–$1,500 (solo) or $4K–$10K (team) ──→ $99–$997/mo retainer
                                                                                                                         ↓
                                                                                                       (some escalate to FusionAL enterprise)
```

---

## Section 1: System Overview

**Three layers:**

| Layer | What it is | Purpose | Build status |
|-------|-----------|---------|--------------|
| Lead Magnet | OSS MCP server + CLI scaffolder, multi-harness | Filters for devs who have the problem | Four new audit tools are the hard work; Recall decoupling is real work too — do not count as ~60–70% done |
| Service | Email capture → audit call → paid implementation → retainer | Where revenue comes from | Funnel infrastructure (domain, landing page, Calendly, pricing page) is launch-blocking — must exist before any public launch |
| Delivery | mcp-consulting-kit + Recall + brain.py + hermes-ui | Fulfillment without rebuilding per client | Already exists, reused as-is |

**Paid value proposition vs. free tool** — state this explicitly so audit call converts:
The free tool detects, scaffolds CLAUDE.md, and generates MCP config. What it cannot do: debug your *specific* broken setup, build custom MCP servers, configure multi-machine sync, or maintain your configs as harness versions change. That is what the service delivers.

---

## Section 2: The Free Tool (Lead Magnet)

### MCP Server — four new tools on top of FusionAL-Recall

FusionAL-Recall (`:8107`) already ships `recall`, `remember`, `list_recent`, `verify`, `get`. The lead-magnet release adds:

| Tool | Input | Output |
|------|-------|--------|
| `audit_harness` | path to harness config dir | JSON report: broken/missing MCP wiring, CLAUDE.md lint, missing memory config |
| `scaffold_claude_md` | harness type, project name | Generated CLAUDE.md tuned for that harness |
| `scaffold_mcp_config` | harness type | Ready-to-paste MCP config block |
| `detect_harness` | current directory | Detected harness(es) + version + known issues |

`harness-optimizer` agent (already built) provides the audit logic. These tools are its JSON-serializable MCP interface.

**Build note:** `audit_harness` is heuristic-heavy, version-sensitive work with an ongoing maintenance tail. It is the majority of the build, not the remainder. Budget accordingly.

**Recall decoupling note:** FusionAL-Recall currently runs as a personal systemd service reading Jonathan's own DB. Decoupling it into a clean installable (fresh DB, no personal data, standalone setup) is real work — not just a sanitizer pass.

### Harness support — v1

**Full support (v1):**
- Claude Code (`~/.claude/` + `CLAUDE.md`) — largest install base, most active MCP discussion, most visible config pain
- Hermes Agent (`~/.hermes/config.yaml`) — Nous Research OSS project (~212K stars, released Feb 2026); self-hosted CLI agent persona matches the "silently broken MCP wiring" buyer exactly; 5-month-old project means first-mover scaffolding room is real; Jonathan runs it daily against a local backend, so audit quality will be credible

**Detection + partial scaffolding (v1.1):**
- Aider (`.aider.conf.yml`)
- Cursor CLI (`~/.cursor/config.json`)
- Cline (VS Code extension config)

Codex CLI: revisit for v2 — growing fast, simple config surface.

### CLI scaffolder — two commands

```bash
agentstack-init init     # detect harness, scaffold CLAUDE.md + MCP config, wire Recall
agentstack-init audit    # run harness-optimizer, output human-readable report + JSON
```

`init` generates:
```
.fusional/
  CLAUDE.md               ← project-specific scaffold
  mcp-config.json         ← wiring block for detected harness
  memory-setup.md         ← instructions for connecting to Recall
  audit-report.json       ← baseline audit, timestamped
```

No auto-write to system dirs in v1 — reduces trust friction. User copies files manually.

### Open-source pipeline (sequential, all agents already built)

1. `opensource-forker` — copies FusionAL-Recall src + new CLI, strips secrets (20+ patterns)
2. `opensource-sanitizer` — scans fork, produces PASS/FAIL before any public push
3. `opensource-packager` — generates README, LICENSE (MIT), CONTRIBUTING.md, `setup.sh`, `CLAUDE.md` for the repo

Publishes under a new GitHub repo separate from FusionAL org — accumulates independent stars/forks/organic traffic.

### Name

**`agentstack-init`** — standalone identity, no FusionAL brand tie. Optimizes for GitHub discoverability ("MCP setup", "Claude Code config", "harness scaffolder", "Hermes MCP"). README links back to FusionAL for the consulting CTA.

---

## Section 3: The Service

### Audit call (free, 30 min)

Developer runs `agentstack-init audit` before booking — arrives with JSON report in hand. Call covers:
- Which MCP servers are connecting vs. silently failing
- Whether CLAUDE.md is being read (and why not if not)
- Current cross-session memory situation (usually: none)
- What a wired setup looks like for their specific workflow

Show starting price on the landing page. A visible price filters better than it deters — it prevents audit calls full of people who like the tool but can't buy the service.

### Implementation tiers

| Tier | Price | Buyer | Scope |
|------|-------|-------|-------|
| **Solo wired session** | **$750–$1,500** | Individual dev, out of pocket | Fixed-scope: one harness wired, Recall deployed, CLAUDE.md tuned, done in a single async session. Card-swipe price point. |
| **Team, single harness** | **$4K** | Dev inside a company, expensable | Claude Code or Hermes wired for a team; shared Recall instance; CLAUDE.md tuned; 1-week async support |
| **Team, multi-harness** | **$5K–7K** | Same | 2–3 harnesses wired and synced; Recall + brain.py deployed; custom MCP server if needed |
| **Team + governance** | **$8K–10K** | Small team (2–5 devs), compliance-aware | All above + FusionAL governance layer; audit trail; onboarding session |

The $750–$1,500 solo tier converts the OSS audience and feeds the retainer. The $4K–$10K tiers target devs who can expense it — reframe as "get your team's harness working."

Delivery uses existing stack: `mcp-consulting-kit` as server templates, Recall as memory, brain.py as orchestration. No new infrastructure per client.

### Retainer

| Tier | Price | Buyer |
|------|-------|-------|
| Solo | **$99–$199/mo** | Individual dev post-wired-session; config maintenance as harness versions change |
| Team | **$750–$997/mo** | Small team; monthly config review, new MCP server additions, CLAUDE.md updates |

Positioned as **ongoing harness maintenance**, not a support contract. Time cost drops after Month 1; Month 2+ is mostly async. Retainer churn is unproven — do not model 5 retainers × $750 as a stable floor until Month 3+ data exists.

---

## Section 4: Distribution / Funnel Mechanics

### In-tool CTA (primary conversion surface)

Every `agentstack-init audit` output ends with:

```
→ Book a free 30-min review: agentstack.fyi/audit
```

CTA lands when pain is live, not abstract. Keep copy understated — HN audiences are hostile to consulting CTAs in free tools; the in-tool message and README CTA should feel like a pointer, not a pitch.

### Email capture (intermediate step — required)

A GitHub star gives no way to reach anyone. Add an intermediate capture step before the audit call:

- **Emailed full report**: `agentstack-init audit --email you@example.com` sends the JSON report with a plain-text summary. One-time email; no drip. Turns tool users into a reachable list.
- Alternatively: a "get fixes changelog" signup on the landing page (new harness support, breaking-change alerts).

Either approach converts passive tool users into contacts without being spammy.

### Distribution channels (in priority order)

**1. MCP registries / directories (highest intent)**
- `awesome-mcp-servers` GitHub list
- Claude Code plugin marketplace / MCP server directory
- modelcontextprotocol.io community page

These are where people *already looking for MCP tooling* search. Submit on launch day, before anything else. Higher intent than any content channel.

**2. GitHub (durable organic base)**
- Demo GIF in README showing before/after audit output
- Title/description optimized for: "MCP setup," "Claude Code config," "Hermes MCP," "harness scaffolder"
- Single CTA button: "Book a free harness audit"

**3. Long-form post (proactive acquisition)**
Two angles — write both:
- *"Why your Hermes MCP servers aren't connecting (and how to fix it)"* — larger, less-served search space; Hermes is 5 months old with 27K open issues
- *"Why your Claude Code MCP servers aren't connecting (and how to fix it)"* — broader audience, more competition

Publish on dev.to. Write after v0.1 ships, link to repo. This does the cold-acquisition work without a sales motion.

**4. Show HN (upside, not launch)**
One post, v0.1 working. Plan the launch as channels 1–3 as the durable base; HN is upside. Most Show HN posts get <10 upvotes — do not treat it as the launch event.

### Measurement (required before launch)

Without measurement you can't distinguish a 2% funnel from a 0.02% one.
- Landing page: install Plausible or Fathom (privacy-friendly, no cookie banner friction) — track `/audit` page visits and Calendly embed clicks
- CLI: no telemetry in the tool itself (dev tool audience is hostile to it), but log audit call completions as a server-side metric if the `--email` flag is used
- Track: tool installs (pip download count), GitHub stars, audit calls booked, audit calls to paid (the only number that matters)

### First-mover window

Near-zero tooling competition in the setup/config gap is real but time-limited. Launch before Q4 2026. **The build order below must have calendar dates — the window drives urgency.**

---

## Section 5: Edge Cases

**"I want the tool, not the service"**  
MIT license, no strings. Self-configuring devs become referral sources and return buyers when their setup breaks. Don't chase them.

**Multi-harness support burden**  
Two config schemas (Claude Code + Hermes) require monitoring for breaking changes. Mitigation: pin to schema versions; add `agentstack-init update-check` to detect harness version drift. Return-visit reason — dev comes back to check, sees CTA again.

**Platform risk (Anthropic ships native `claude setup`)**  
Scaffolder becomes redundant. Service doesn't — the moat is done-for-you delivery + debugging expertise, not the CLI. Acceptable risk.

**Price anchor mismatch**  
The funnel attracts OSS/CLI devs via a free tool; quoting $4K on an audit call loses them. The $750–$1,500 solo tier is the conversion bridge. If audit calls convert below 20%, check whether the tier is visible on the landing page before the call.

---

## Build Order

1. **MCP server** (4 new tools on top of FusionAL-Recall) — `audit_harness` is the hard work; Recall decoupling is a distinct sub-task
2. **CLI scaffolder** (`agentstack-init init` + `audit` + `update-check`)
3. **Funnel infrastructure** — register `agentstack.fyi`, build landing page (visible pricing, Calendly embed, email capture), write tier one-pager — **launch-blocking; run in parallel with steps 1–2, must be done before step 4**
4. **Run opensource pipeline** (forker → sanitizer → packager)
5. **Publish** — GitHub repo, MCP registry submissions (same day), dev.to posts
6. Show HN (as upside, once repo has traction)
7. Web dashboard (hermes-ui adapted) — Phase 3
8. VS Code extension — Phase 4

---

## Open Questions / Out of Scope

- `agentstack.fyi` domain — register now, not at launch
- Email provider for the `--email` flag (Resend or Postmark; 1-day integration)
- VS Code extension: out of scope until v2
- Community/Discord: deferred (low priority)
