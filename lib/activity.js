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

const DAYS = 31;
const WIDTH = 850;
const HEIGHT = 320;
const PAD_L = 48;
const PAD_R = 28;
const PAD_T = 56;
const PAD_B = 44;

export async function fetchRecentDays(login = USERNAME, n = DAYS) {
  const data = await gql(
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
  const days = [];
  const today = new Date().toISOString().slice(0, 10);
  for (const week of data.user.contributionsCollection.contributionCalendar
    .weeks) {
    for (const day of week.contributionDays) {
      if (day.date <= today) days.push(day);
    }
  }
  return days.slice(-n);
}

function polylinePoints(values, maxV) {
  const chartW = WIDTH - PAD_L - PAD_R;
  const chartH = HEIGHT - PAD_T - PAD_B;
  const n = values.length;
  const xs =
    n === 1
      ? [PAD_L + chartW / 2]
      : values.map((_, i) => PAD_L + (i * chartW) / (n - 1));
  const pts = values.map((v, i) => {
    const y = PAD_T + chartH - (maxV === 0 ? 0 : (v / maxV) * chartH);
    return `${xs[i].toFixed(2)},${y.toFixed(2)}`;
  });
  return { points: pts.join(" "), xs };
}

export function renderActivitySvg(days) {
  const values = days.map((d) => d.contributionCount);
  const maxRaw = values.length ? Math.max(...values) : 1;
  const yMax = maxRaw <= 5 ? 5 : maxRaw <= 10 ? 10 : Math.ceil(maxRaw / 10) * 10;
  const { points, xs } = polylinePoints(values, yMax);
  const chartH = HEIGHT - PAD_T - PAD_B;
  const yTicks = [0, Math.floor(yMax / 2), yMax];

  let lastMonth = null;
  const xLabels = [];
  days.forEach((day, i) => {
    const m = Number(day.date.slice(5, 7));
    if (m !== lastMonth) {
      xLabels.push({ x: xs[i], label: MONTHS[m - 1] });
      lastMonth = m;
    }
  });

  const area =
    xs.length === 0
      ? ""
      : `${xs[0].toFixed(2)},${(PAD_T + chartH).toFixed(2)} ${points} ${xs[
          xs.length - 1
        ].toFixed(2)},${(PAD_T + chartH).toFixed(2)}`;

  const yLabels = yTicks
    .map(
      (v) =>
        `<text x="${PAD_L - 12}" y="${(
          PAD_T +
          chartH -
          (v / yMax) * chartH +
          4
        ).toFixed(2)}" text-anchor="end" fill="#8b949e" font-size="12" font-family="Segoe UI, Ubuntu, sans-serif">${v}</text>`
    )
    .join("\n");

  const grid = yTicks
    .map(
      (v) =>
        `<line x1="${PAD_L}" y1="${(
          PAD_T +
          chartH -
          (v / yMax) * chartH
        ).toFixed(2)}" x2="${WIDTH - PAD_R}" y2="${(
          PAD_T +
          chartH -
          (v / yMax) * chartH
        ).toFixed(2)}" stroke="#21262d" stroke-width="1"/>`
    )
    .join("\n");

  const xLabelSvg = xLabels
    .map(
      ({ x, label }) =>
        `<text x="${x.toFixed(
          2
        )}" y="${HEIGHT - 16}" text-anchor="middle" fill="#8b949e" font-size="12" font-family="Segoe UI, Ubuntu, sans-serif">${label}</text>`
    )
    .join("\n");

  const dots = values
    .map(
      (v, i) =>
        `<circle cx="${xs[i].toFixed(2)}" cy="${(
          PAD_T +
          chartH -
          (v / yMax) * chartH
        ).toFixed(2)}" r="3.5" fill="#fb7185"/>`
    )
    .join("\n");

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-label="Contribution activity">
  <rect width="100%" height="100%" fill="#0d1117" rx="6"/>
  <text x="${WIDTH / 2}" y="28" text-anchor="middle" fill="#c9d1d9" font-size="16" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">Contribution Activity</text>
  ${grid}
  ${yLabels}
  <polygon points="${area}" fill="#e11d48" fill-opacity="0.12"/>
  <polyline points="${points}" fill="none" stroke="#e11d48" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
  ${dots}
  ${xLabelSvg}
</svg>`;
}
