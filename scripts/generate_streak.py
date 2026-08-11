#!/usr/bin/env python3
"""Generate a github-readme-streak-stats-style SVG from live GitHub GraphQL data."""

from __future__ import annotations

import json
import os
import urllib.request
from calendar import month_abbr
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "shrey1110-dotcom")
OUT = Path(__file__).resolve().parents[1] / "assets" / "github-streak.svg"


def gql(token: str, query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "shrey1110-dotcom-streak",
        },
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fmt_day(d: date, include_year: bool) -> str:
    label = f"{month_abbr[d.month]} {d.day}"
    if include_year:
        label = f"{label}, {d.year}"
    return label


def fmt_range(start: date | None, end: date | None, present: bool = False) -> str:
    if start is None:
        return ""
    if present:
        return f"{fmt_day(start, True)} - Present"
    assert end is not None
    if start == end:
        same_year = start.year == date.today().year
        return fmt_day(start, not same_year)
    include_year = start.year != end.year or end.year != date.today().year
    if start.year == end.year and not include_year:
        return f"{fmt_day(start, False)} - {fmt_day(end, False)}"
    return f"{fmt_day(start, True)} - {fmt_day(end, True)}"


def compute_stats(by_day: dict[str, int]) -> dict:
    today = date.today()
    first = None
    for key in sorted(by_day):
        if by_day[key] > 0:
            first = date.fromisoformat(key)
            break

    total = sum(by_day.values())

    # Current streak (match common streak-stats behavior: allow missing today)
    cursor = today
    if by_day.get(cursor.isoformat(), 0) == 0:
        cursor = today - timedelta(days=1)
    current = 0
    current_end = cursor if by_day.get(cursor.isoformat(), 0) > 0 else None
    while by_day.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    current_start = cursor + timedelta(days=1) if current else None

    longest = 0
    longest_start = None
    longest_end = None
    run = 0
    run_start = None
    day = first or today
    while day <= today:
        if by_day.get(day.isoformat(), 0) > 0:
            if run == 0:
                run_start = day
            run += 1
            if run > longest:
                longest = run
                longest_start = run_start
                longest_end = day
        else:
            run = 0
            run_start = None
        day += timedelta(days=1)

    return {
        "total": total,
        "first": first,
        "current": current,
        "current_start": current_start,
        "current_end": current_end,
        "longest": longest,
        "longest_start": longest_start,
        "longest_end": longest_end,
    }


def render_svg(stats: dict) -> str:
    total = f"{stats['total']:,}"
    current = str(stats["current"])
    longest = str(stats["longest"])
    total_range = fmt_range(stats["first"], None, present=True)
    if stats["current"]:
        current_range = fmt_range(stats["current_start"], stats["current_end"])
    else:
        current_range = fmt_day(date.today(), False)
    longest_range = fmt_range(stats["longest_start"], stats["longest_end"])

    return f"""<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'
                style='isolation: isolate' viewBox='0 0 495 195' width='495px' height='195px' direction='ltr'>
        <style>
            @keyframes currstreak {{
                0% {{ font-size: 3px; opacity: 0.2; }}
                80% {{ font-size: 34px; opacity: 1; }}
                100% {{ font-size: 28px; opacity: 1; }}
            }}
            @keyframes fadein {{
                0% {{ opacity: 0; }}
                100% {{ opacity: 1; }}
            }}
        </style>
        <defs>
            <clipPath id='outer_rectangle'>
                <rect width='495' height='195' rx='4.5'/>
            </clipPath>
            <mask id='mask_out_ring_behind_fire'>
                <rect width='495' height='195' fill='white'/>
                <ellipse id='mask-ellipse' cx='247.5' cy='32' rx='13' ry='18' fill='black'/>
            </mask>
        </defs>
        <g clip-path='url(#outer_rectangle)'>
            <g style='isolation: isolate'>
                <rect stroke='#000000' stroke-opacity='0' fill='#151515' rx='4.5' x='0.5' y='0.5' width='494' height='194'/>
            </g>
            <g style='isolation: isolate'>
                <line x1='165' y1='28' x2='165' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#E4E2E2' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
                <line x1='330' y1='28' x2='330' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#E4E2E2' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
            </g>
            <g style='isolation: isolate'>
                <g transform='translate(82.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FEFEFE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>
                        {total}
                    </text>
                </g>
                <g transform='translate(82.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FEFEFE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.7s'>
                        Total Contributions
                    </text>
                </g>
                <g transform='translate(82.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#9E9E9E' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.8s'>
                        {total_range}
                    </text>
                </g>
            </g>
            <g style='isolation: isolate'>
                <g transform='translate(247.5, 108)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FF6A00' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>
                        Current Streak
                    </text>
                </g>
                <g transform='translate(247.5, 145)'>
                    <text x='0' y='21' stroke-width='0' text-anchor='middle' fill='#9E9E9E' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>
                        {current_range}
                    </text>
                </g>
                <g mask='url(#mask_out_ring_behind_fire)'>
                    <circle cx='247.5' cy='71' r='40' fill='none' stroke='#FF4500' stroke-width='5' style='opacity: 0; animation: fadein 0.5s linear forwards 0.4s'></circle>
                </g>
                <g transform='translate(247.5, 19.5)' stroke-opacity='0' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>
                    <path d='M -12 -0.5 L 15 -0.5 L 15 23.5 L -12 23.5 L -12 -0.5 Z' fill='none'/>
                    <path d='M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z' fill='#FF1E00' stroke-opacity='0'/>
                </g>
                <g transform='translate(247.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FFFFFF' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='animation: currstreak 0.6s linear forwards'>
                        {current}
                    </text>
                </g>
            </g>
            <g style='isolation: isolate'>
                <g transform='translate(412.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FEFEFE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.2s'>
                        {longest}
                    </text>
                </g>
                <g transform='translate(412.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FEFEFE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.3s'>
                        Longest Streak
                    </text>
                </g>
                <g transform='translate(412.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#9E9E9E' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.4s'>
                        {longest_range}
                    </text>
                </g>
            </g>
        </g>
    </svg>
"""


def _ingest_weeks(by_day: dict[str, int], weeks: list) -> None:
    for week in weeks:
        for day in week["contributionDays"]:
            # Prefer the higher count when windows overlap / disagree
            by_day[day["date"]] = max(
                by_day.get(day["date"], 0), day["contributionCount"]
            )


def fetch_days(token: str, login: str) -> dict[str, int]:
    meta = gql(
        token,
        """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection { contributionYears }
          }
        }
        """,
        {"login": login},
    )
    years = meta["user"]["contributionsCollection"]["contributionYears"]
    by_day: dict[str, int] = {}
    q = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    for year in sorted(set(years)):
        data = gql(
            token,
            q,
            {
                "login": login,
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year}-12-31T23:59:59Z",
            },
        )
        weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        _ingest_weeks(by_day, weeks)

    # Year-bounded calendars can under-count "today"; overlay the default window.
    recent = gql(
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
    _ingest_weeks(
        by_day,
        recent["user"]["contributionsCollection"]["contributionCalendar"]["weeks"],
    )
    return by_day


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN or GH_TOKEN is required")

    by_day = fetch_days(token, USERNAME)
    stats = compute_stats(by_day)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_svg(stats), encoding="utf-8")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "generated_at": generated,
                "total": stats["total"],
                "current": stats["current"],
                "longest": stats["longest"],
            }
        )
    )


if __name__ == "__main__":
    main()
