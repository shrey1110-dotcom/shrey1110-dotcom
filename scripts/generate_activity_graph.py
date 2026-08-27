#!/usr/bin/env python3
"""Generate a contribution activity line chart SVG from live GitHub GraphQL data."""

from __future__ import annotations

import json
import os
import urllib.request
from calendar import month_abbr
from datetime import date, datetime, timezone
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "shrey1110-dotcom")
OUT = Path(__file__).resolve().parents[1] / "assets" / "activity-graph.svg"
DAYS = 31
WIDTH = 850
HEIGHT = 320
PAD_L, PAD_R, PAD_T, PAD_B = 48, 28, 56, 44


def gql(token: str, query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "shrey1110-dotcom-activity-graph",
        },
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch_recent_days(token: str, login: str, n: int) -> list[dict]:
    data = gql(
        token,
        """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar {
                weeks {
                  contributionDays { date contributionCount }
                }
              }
            }
          }
        }
        """,
        {"login": login},
    )
    days = []
    weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    for week in weeks:
        for day in week["contributionDays"]:
            if date.fromisoformat(day["date"]) <= date.today():
                days.append(day)
    return days[-n:]


def polyline_points(values: list[int], max_v: int) -> str:
    chart_w = WIDTH - PAD_L - PAD_R
    chart_h = HEIGHT - PAD_T - PAD_B
    n = len(values)
    if n == 1:
        xs = [PAD_L + chart_w / 2]
    else:
        xs = [PAD_L + (i * chart_w / (n - 1)) for i in range(n)]
    pts = []
    for x, v in zip(xs, values):
        y = PAD_T + chart_h - (0 if max_v == 0 else (v / max_v) * chart_h)
        pts.append(f"{x:.2f},{y:.2f}")
    return " ".join(pts), xs


def month_ticks(days: list[dict], xs: list[float]) -> list[tuple[float, str]]:
    ticks = []
    last_month = None
    for i, day in enumerate(days):
        d = date.fromisoformat(day["date"])
        if d.month != last_month:
            ticks.append((xs[i], month_abbr[d.month]))
            last_month = d.month
    return ticks


def render_svg(days: list[dict]) -> str:
    values = [d["contributionCount"] for d in days]
    max_v = max(values) if values else 1
    # Nice y-axis ceiling
    if max_v <= 5:
        y_max = 5
    elif max_v <= 10:
        y_max = 10
    else:
        y_max = int((max_v + 9) // 10 * 10)
    points, xs = polyline_points(values, y_max)
    chart_h = HEIGHT - PAD_T - PAD_B
    y_ticks = [0, y_max // 2, y_max]
    x_labels = month_ticks(days, xs)

    # Area fill under the line
    area = points
    if xs:
        area = (
            f"{xs[0]:.2f},{PAD_T + chart_h:.2f} "
            + points
            + f" {xs[-1]:.2f},{PAD_T + chart_h:.2f}"
        )

    y_labels = "\n".join(
        f'<text x="{PAD_L - 12}" y="{PAD_T + chart_h - (v / y_max) * chart_h + 4:.2f}" '
        f'text-anchor="end" fill="#8b949e" font-size="12" '
        f'font-family="Segoe UI, Ubuntu, sans-serif">{v}</text>'
        for v in y_ticks
    )
    grid = "\n".join(
        f'<line x1="{PAD_L}" y1="{PAD_T + chart_h - (v / y_max) * chart_h:.2f}" '
        f'x2="{WIDTH - PAD_R}" y2="{PAD_T + chart_h - (v / y_max) * chart_h:.2f}" '
        f'stroke="#21262d" stroke-width="1"/>'
        for v in y_ticks
    )
    x_label_svg = "\n".join(
        f'<text x="{x:.2f}" y="{HEIGHT - 16}" text-anchor="middle" fill="#8b949e" '
        f'font-size="12" font-family="Segoe UI, Ubuntu, sans-serif">{label}</text>'
        for x, label in x_labels
    )
    dots = "\n".join(
        f'<circle cx="{x:.2f}" cy="{PAD_T + chart_h - (v / y_max) * chart_h:.2f}" '
        f'r="3.5" fill="#fb7185"/>'
        for x, v in zip(xs, values)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Contribution activity">
  <rect width="100%" height="100%" fill="#0d1117" rx="6"/>
  <text x="{WIDTH / 2}" y="28" text-anchor="middle" fill="#c9d1d9" font-size="16" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">Contribution Activity</text>
  {grid}
  {y_labels}
  <polygon points="{area}" fill="#e11d48" fill-opacity="0.12"/>
  <polyline points="{points}" fill="none" stroke="#e11d48" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
  {dots}
  {x_label_svg}
</svg>
"""


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN or GH_TOKEN is required")

    days = fetch_recent_days(token, USERNAME, DAYS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_svg(days), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "days": len(days),
                "total": sum(d["contributionCount"] for d in days),
                "max": max((d["contributionCount"] for d in days), default=0),
            }
        )
    )


if __name__ == "__main__":
    main()
