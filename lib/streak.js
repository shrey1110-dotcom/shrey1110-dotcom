import { gql, USERNAME } from "./github.js";

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function fmtDay(d, includeYear) {
  const label = `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}`;
  return includeYear ? `${label}, ${d.getUTCFullYear()}` : label;
}

function fmtRange(start, end, present = false) {
  if (!start) return "";
  if (present) return `${fmtDay(start, true)} - Present`;
  if (start.getTime() === end.getTime()) {
    const sameYear = start.getUTCFullYear() === new Date().getUTCFullYear();
    return fmtDay(start, !sameYear);
  }
  const includeYear =
    start.getUTCFullYear() !== end.getUTCFullYear() ||
    end.getUTCFullYear() !== new Date().getUTCFullYear();
  if (start.getUTCFullYear() === end.getUTCFullYear() && !includeYear) {
    return `${fmtDay(start, false)} - ${fmtDay(end, false)}`;
  }
  return `${fmtDay(start, true)} - ${fmtDay(end, true)}`;
}

function toDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function iso(d) {
  return d.toISOString().slice(0, 10);
}

function addDays(d, n) {
  const x = new Date(d.getTime());
  x.setUTCDate(x.getUTCDate() + n);
  return x;
}

function ingestWeeks(byDay, weeks) {
  for (const week of weeks) {
    for (const day of week.contributionDays) {
      byDay[day.date] = Math.max(byDay[day.date] || 0, day.contributionCount);
    }
  }
}

export async function fetchContributionDays(login = USERNAME) {
  const meta = await gql(
    `query($login: String!) {
      user(login: $login) {
        contributionsCollection { contributionYears }
      }
    }`,
    { login }
  );
  const years = meta.user.contributionsCollection.contributionYears;
  const byDay = {};
  const yearQuery = `query($login: String!, $from: DateTime!, $to: DateTime!) {
    user(login: $login) {
      contributionsCollection(from: $from, to: $to) {
        contributionCalendar {
          weeks { contributionDays { date contributionCount } }
        }
      }
    }
  }`;
  for (const year of [...new Set(years)].sort()) {
    const data = await gql(yearQuery, {
      login,
      from: `${year}-01-01T00:00:00Z`,
      to: `${year}-12-31T23:59:59Z`,
    });
    ingestWeeks(
      byDay,
      data.user.contributionsCollection.contributionCalendar.weeks
    );
  }
  const recent = await gql(
    `query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }`,
    { login }
  );
  ingestWeeks(
    byDay,
    recent.user.contributionsCollection.contributionCalendar.weeks
  );
  return byDay;
}

export function computeStats(byDay) {
  const today = toDate(iso(new Date()));
  let first = null;
  for (const key of Object.keys(byDay).sort()) {
    if (byDay[key] > 0) {
      first = toDate(key);
      break;
    }
  }
  const total = Object.values(byDay).reduce((a, b) => a + b, 0);

  let cursor = today;
  if ((byDay[iso(cursor)] || 0) === 0) cursor = addDays(today, -1);
  let current = 0;
  let currentEnd = (byDay[iso(cursor)] || 0) > 0 ? cursor : null;
  while ((byDay[iso(cursor)] || 0) > 0) {
    current += 1;
    cursor = addDays(cursor, -1);
  }
  const currentStart = current ? addDays(cursor, 1) : null;

  let longest = 0;
  let longestStart = null;
  let longestEnd = null;
  let run = 0;
  let runStart = null;
  let day = first || today;
  while (day <= today) {
    if ((byDay[iso(day)] || 0) > 0) {
      if (run === 0) runStart = day;
      run += 1;
      if (run > longest) {
        longest = run;
        longestStart = runStart;
        longestEnd = day;
      }
    } else {
      run = 0;
      runStart = null;
    }
    day = addDays(day, 1);
  }

  return {
    total,
    first,
    current,
    currentStart,
    currentEnd,
    longest,
    longestStart,
    longestEnd,
  };
}

export function renderStreakSvg(stats) {
  const total = stats.total.toLocaleString("en-US");
  const current = String(stats.current);
  const longest = String(stats.longest);
  const totalRange = fmtRange(stats.first, null, true);
  const currentRange = stats.current
    ? fmtRange(stats.currentStart, stats.currentEnd)
    : fmtDay(toDate(iso(new Date())), false);
  const longestRange = fmtRange(stats.longestStart, stats.longestEnd);

  return `<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'
                style='isolation: isolate' viewBox='0 0 495 195' width='495px' height='195px' direction='ltr'>
        <style>
            @keyframes currstreak {
                0% { font-size: 3px; opacity: 0.2; }
                80% { font-size: 34px; opacity: 1; }
                100% { font-size: 28px; opacity: 1; }
            }
            @keyframes fadein {
                0% { opacity: 0; }
                100% { opacity: 1; }
            }
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
                        ${total}
                    </text>
                </g>
                <g transform='translate(82.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FEFEFE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.7s'>
                        Total Contributions
                    </text>
                </g>
                <g transform='translate(82.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#9E9E9E' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.8s'>
                        ${totalRange}
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
                        ${currentRange}
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
                        ${current}
                    </text>
                </g>
            </g>
            <g style='isolation: isolate'>
                <g transform='translate(412.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FEFEFE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.2s'>
                        ${longest}
                    </text>
                </g>
                <g transform='translate(412.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#FEFEFE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.3s'>
                        Longest Streak
                    </text>
                </g>
                <g transform='translate(412.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#9E9E9E' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.4s'>
                        ${longestRange}
                    </text>
                </g>
            </g>
        </g>
    </svg>`;
}
