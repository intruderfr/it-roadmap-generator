# IT Roadmap Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

Generate a polished, self-contained HTML executive roadmap report from a simple YAML file.
Built for CIOs, CTOs, and Heads of IT who need to communicate the multi-quarter technology
strategy to executive committees, boards, and steering groups — without spending a week
in PowerPoint.

> **Author:** Aslam Ahamed — Head of IT @ Prestige One Developments, Dubai
> **LinkedIn:** [aslam-ahamed](https://www.linkedin.com/in/aslam-ahamed/)

---

## What it does

You write your roadmap once in YAML. The tool produces:

1. **A board-ready HTML report** — fully self-contained (no external CSS/JS), opens in any
   browser, prints cleanly to PDF, and emails as a single attachment.
2. **A quarter-by-quarter Gantt timeline** — initiatives rendered as bars across Q1-Q4
   with RAG (red/amber/green) status colours.
3. **Executive KPI cards** — total budget, count of initiatives, status distribution,
   pillar mix.
4. **A pillar breakdown** — group your investment by IT pillar (Cloud, Security, Data,
   etc.) so the audience can see where the money is going.
5. **A risks register** — top risks rolled up across all initiatives with an owner column.
6. **A detail table** — every initiative with budget, owner, status, dependencies and KPIs.

You can also export the same data as a JSON file for downstream consumption (BI dashboards,
PMO trackers, board portal upload, etc.).

## Installation

```bash
git clone https://github.com/intruderfr/it-roadmap-generator.git
cd it-roadmap-generator
pip install -r requirements.txt
```

Python 3.10 or newer is required (uses `match`/`case` and modern typing).

## Quick start

```bash
# Generate an HTML report from the bundled sample
python roadmap.py build examples/sample-roadmap.yaml --out roadmap.html

# Open in your default browser
python roadmap.py build examples/sample-roadmap.yaml --out roadmap.html --open

# Export to JSON instead (for ingestion into PMO tools)
python roadmap.py export examples/sample-roadmap.yaml --format json --out roadmap.json

# Validate a YAML file without rendering
python roadmap.py validate examples/sample-roadmap.yaml
```

## YAML schema

```yaml
organization:
  name: Acme Holdings
  fiscal_year: 2026
  prepared_by: Jane Doe, CIO
  prepared_on: 2026-01-15

initiatives:
  - id: INIT-001
    name: Migrate CRM to AWS
    pillar: Cloud
    owner: Aslam Ahamed
    status: green                    # green | amber | red | done | not-started
    quarters: [Q1, Q2]               # one or more of Q1..Q4
    budget: 250000                   # in your reporting currency
    description: >
      Lift-and-shift the legacy on-prem CRM onto AWS RDS+ECS. Delivers
      99.9% uptime SLA and removes the colocation contract.
    dependencies: []                 # list of other INIT- ids
    risks:
      - Vendor SLA gaps
      - Data residency review pending
    kpis:
      - 99.9% uptime
      - p95 latency under 50 ms
      - 30% TCO reduction year-on-year
```

`status` legend:

| Status | Meaning |
|--------|---------|
| `green` | On track |
| `amber` | At risk — mitigation in flight |
| `red` | Off track — escalation required |
| `done` | Complete |
| `not-started` | Not yet kicked off |

## Commands

| Command | Purpose |
|---------|---------|
| `roadmap.py build FILE` | Render a roadmap YAML into an HTML report |
| `roadmap.py validate FILE` | Validate the YAML against the schema and print a summary |
| `roadmap.py export FILE` | Export the parsed roadmap as JSON or CSV |
| `roadmap.py new` | Print a starter YAML template to stdout |

Run any command with `--help` for the full set of flags.

## Why YAML?

Most IT leaders already keep a spreadsheet of initiatives. YAML gives you:

* Version control via Git — every change to the roadmap is reviewable and reversible.
* No proprietary lock-in — works with any text editor.
* Diff-friendly — quarterly business reviews can show what changed week-over-week.
* CI-friendly — drop the YAML into a repo, generate the HTML in a pipeline, publish to
  the intranet automatically.

## Running the tests

```bash
pip install -r requirements.txt
python -m pytest tests/
```

## License

MIT — see `LICENSE`.

## Contributing

Pull requests welcome. If you build a real roadmap with this tool and discover a missing
field (e.g., OKR mapping, business-unit owner, regulatory driver), open an issue or PR.
