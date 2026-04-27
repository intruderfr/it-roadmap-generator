#!/usr/bin/env python3
"""IT Roadmap Generator.

Render a YAML roadmap of IT initiatives into an executive-ready HTML report.

Author: Aslam Ahamed - Head of IT @ Prestige One Developments, Dubai
LinkedIn: https://www.linkedin.com/in/aslam-ahamed/
License: MIT
"""

from __future__ import annotations

import csv
import json
import sys
import webbrowser
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import click
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

VALID_QUARTERS = ("Q1", "Q2", "Q3", "Q4")
VALID_STATUSES = ("green", "amber", "red", "done", "not-started")

STATUS_COLORS = {
    "green": "#16a34a",
    "amber": "#f59e0b",
    "red": "#dc2626",
    "done": "#0ea5e9",
    "not-started": "#94a3b8",
}

STATUS_LABELS = {
    "green": "On track",
    "amber": "At risk",
    "red": "Off track",
    "done": "Complete",
    "not-started": "Not started",
}

THIS_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = THIS_DIR / "templates"


@dataclass
class Initiative:
    id: str
    name: str
    pillar: str
    owner: str
    status: str
    quarters: list[str]
    budget: float = 0.0
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    kpis: list[str] = field(default_factory=list)

    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)

    def status_color(self) -> str:
        return STATUS_COLORS.get(self.status, "#64748b")


@dataclass
class Organization:
    name: str = "Organization"
    fiscal_year: int = 2026
    prepared_by: str = ""
    prepared_on: str = ""


@dataclass
class Roadmap:
    organization: Organization
    initiatives: list[Initiative]

    def total_budget(self) -> float:
        return sum(i.budget for i in self.initiatives)

    def status_counts(self) -> dict[str, int]:
        c: Counter = Counter(i.status for i in self.initiatives)
        return {s: c.get(s, 0) for s in VALID_STATUSES}

    def pillar_breakdown(self) -> list[dict[str, Any]]:
        groups: dict[str, list[Initiative]] = defaultdict(list)
        for i in self.initiatives:
            groups[i.pillar].append(i)
        rows = []
        for pillar, items in groups.items():
            rows.append({
                "pillar": pillar,
                "count": len(items),
                "budget": sum(i.budget for i in items),
            })
        rows.sort(key=lambda r: r["budget"], reverse=True)
        return rows

    def all_risks(self) -> list[dict[str, str]]:
        out = []
        for i in self.initiatives:
            for r in i.risks:
                out.append({"risk": r, "initiative": i.name, "owner": i.owner})
        return out


class RoadmapError(Exception):
    """Raised when a roadmap YAML file is invalid."""


def load_roadmap(path: Path) -> Roadmap:
    if not path.exists():
        raise RoadmapError(f"File not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_roadmap(raw)


def parse_roadmap(raw: dict[str, Any]) -> Roadmap:
    if not isinstance(raw, dict):
        raise RoadmapError("Top-level YAML must be a mapping/dict.")

    org_data = raw.get("organization") or {}
    org = Organization(
        name=str(org_data.get("name", "Organization")),
        fiscal_year=int(org_data.get("fiscal_year", 2026)),
        prepared_by=str(org_data.get("prepared_by", "")),
        prepared_on=str(org_data.get("prepared_on", "")),
    )

    initiatives_raw = raw.get("initiatives") or []
    if not isinstance(initiatives_raw, list):
        raise RoadmapError("`initiatives` must be a list.")

    initiatives: list[Initiative] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(initiatives_raw):
        if not isinstance(item, dict):
            raise RoadmapError(f"initiative #{idx}: must be a mapping/dict.")
        ini = _parse_initiative(item, idx)
        if ini.id in seen_ids:
            raise RoadmapError(f"Duplicate initiative id: {ini.id}")
        seen_ids.add(ini.id)
        initiatives.append(ini)

    for ini in initiatives:
        for dep in ini.dependencies:
            if dep not in seen_ids:
                raise RoadmapError(
                    f"{ini.id}: dependency '{dep}' is not a known initiative id"
                )

    return Roadmap(organization=org, initiatives=initiatives)


def _parse_initiative(item: dict[str, Any], idx: int) -> Initiative:
    required = ["id", "name", "pillar", "owner", "status", "quarters"]
    missing = [k for k in required if k not in item]
    if missing:
        raise RoadmapError(
            f"initiative #{idx}: missing required field(s): {', '.join(missing)}"
        )

    status = str(item["status"]).lower()
    if status not in VALID_STATUSES:
        raise RoadmapError(
            f"initiative {item['id']}: status '{status}' must be one of "
            f"{', '.join(VALID_STATUSES)}"
        )

    quarters_raw = item["quarters"]
    if isinstance(quarters_raw, str):
        quarters = [quarters_raw.strip().upper()]
    elif isinstance(quarters_raw, list):
        quarters = [str(q).strip().upper() for q in quarters_raw]
    else:
        raise RoadmapError(
            f"initiative {item['id']}: 'quarters' must be a string or list"
        )
    for q in quarters:
        if q not in VALID_QUARTERS:
            raise RoadmapError(
                f"initiative {item['id']}: quarter '{q}' must be one of "
                f"{', '.join(VALID_QUARTERS)}"
            )

    try:
        budget = float(item.get("budget", 0) or 0)
    except (TypeError, ValueError) as exc:
        raise RoadmapError(
            f"initiative {item['id']}: budget must be a number"
        ) from exc

    return Initiative(
        id=str(item["id"]),
        name=str(item["name"]),
        pillar=str(item["pillar"]),
        owner=str(item["owner"]),
        status=status,
        quarters=quarters,
        budget=budget,
        description=str(item.get("description", "")).strip(),
        dependencies=[str(d) for d in (item.get("dependencies") or [])],
        risks=[str(r) for r in (item.get("risks") or [])],
        kpis=[str(k) for k in (item.get("kpis") or [])],
    )


def _format_currency(value: float) -> str:
    if value >= 1_000_000:
        return f"${value/1_000_000:,.2f}M"
    if value >= 1_000:
        return f"${value/1_000:,.0f}K"
    return f"${value:,.0f}"


def render_html(roadmap: Roadmap) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["currency"] = _format_currency

    template = env.get_template("report.html")
    return template.render(
        org=roadmap.organization,
        initiatives=roadmap.initiatives,
        total_budget=roadmap.total_budget(),
        status_counts=roadmap.status_counts(),
        status_colors=STATUS_COLORS,
        status_labels=STATUS_LABELS,
        pillar_breakdown=roadmap.pillar_breakdown(),
        all_risks=roadmap.all_risks(),
        quarters=VALID_QUARTERS,
    )


def render_json(roadmap: Roadmap) -> str:
    payload = {
        "organization": asdict(roadmap.organization),
        "initiatives": [asdict(i) for i in roadmap.initiatives],
        "summary": {
            "total_budget": roadmap.total_budget(),
            "initiative_count": len(roadmap.initiatives),
            "status_counts": roadmap.status_counts(),
            "pillar_breakdown": roadmap.pillar_breakdown(),
        },
    }
    return json.dumps(payload, indent=2)


def render_csv(roadmap: Roadmap) -> str:
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "name", "pillar", "owner", "status", "quarters",
        "budget", "dependencies", "risks", "kpis", "description",
    ])
    for i in roadmap.initiatives:
        writer.writerow([
            i.id, i.name, i.pillar, i.owner, i.status,
            "; ".join(i.quarters), f"{i.budget:.2f}",
            "; ".join(i.dependencies), "; ".join(i.risks),
            "; ".join(i.kpis), i.description.replace("\n", " "),
        ])
    return buf.getvalue()


STARTER_YAML = """\
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
    status: green
    quarters: [Q1, Q2]
    budget: 250000
    description: Lift-and-shift the legacy CRM onto AWS RDS+ECS.
    dependencies: []
    risks:
      - Vendor SLA gaps
    kpis:
      - 99.9% uptime
      - p95 latency under 50 ms

  - id: INIT-002
    name: Roll out MFA company-wide
    pillar: Cybersecurity
    owner: Security Team
    status: amber
    quarters: [Q1]
    budget: 45000
    dependencies: []
    risks:
      - Field-staff device coverage
    kpis:
      - 100% workforce enrolled by end of Q1
"""


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option("1.0.0", prog_name="it-roadmap-generator")
def cli() -> None:
    """Generate executive IT roadmap reports from a YAML file."""


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--out", "output", type=click.Path(dir_okay=False, path_type=Path),
              default=Path("roadmap.html"), show_default=True,
              help="Path to write the HTML report to.")
@click.option("--open", "open_browser", is_flag=True,
              help="Open the rendered HTML in the default browser when done.")
def build(input_file: Path, output: Path, open_browser: bool) -> None:
    """Build an HTML roadmap report from INPUT_FILE."""
    try:
        roadmap = load_roadmap(input_file)
    except RoadmapError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    html = render_html(roadmap)
    output.write_text(html, encoding="utf-8")

    click.echo(f"Wrote {output} ({len(html):,} bytes)")
    click.echo(f"  Initiatives: {len(roadmap.initiatives)}")
    click.echo(f"  Total budget: {_format_currency(roadmap.total_budget())}")

    if open_browser:
        webbrowser.open(output.resolve().as_uri())


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def validate(input_file: Path) -> None:
    """Validate INPUT_FILE against the roadmap schema."""
    try:
        roadmap = load_roadmap(input_file)
    except RoadmapError as exc:
        click.echo(f"INVALID: {exc}", err=True)
        sys.exit(1)

    click.echo("VALID")
    click.echo(f"  Organization: {roadmap.organization.name} (FY{roadmap.organization.fiscal_year})")
    click.echo(f"  Initiatives:  {len(roadmap.initiatives)}")
    click.echo(f"  Total budget: {_format_currency(roadmap.total_budget())}")
    sc = roadmap.status_counts()
    bits = ", ".join(f"{STATUS_LABELS[k]}: {v}" for k, v in sc.items() if v)
    click.echo(f"  Status mix:   {bits or '(empty)'}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-f", "--format", "fmt", type=click.Choice(["json", "csv"]),
              default="json", show_default=True)
@click.option("-o", "--out", "output", type=click.Path(dir_okay=False, path_type=Path))
def export(input_file: Path, fmt: str, output: Path | None) -> None:
    """Export the parsed roadmap as JSON or CSV."""
    try:
        roadmap = load_roadmap(input_file)
    except RoadmapError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    rendered = render_json(roadmap) if fmt == "json" else render_csv(roadmap)

    if output is None:
        click.echo(rendered)
    else:
        output.write_text(rendered, encoding="utf-8")
        click.echo(f"Wrote {output} ({len(rendered):,} bytes)")


@cli.command()
def new() -> None:
    """Print a starter YAML template to stdout."""
    click.echo(STARTER_YAML)


if __name__ == "__main__":
    cli()
