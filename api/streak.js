import { svgResponse, errorSvg } from "../lib/github.js";
import {
  fetchContributionDays,
  computeStats,
  renderStreakSvg,
} from "../lib/streak.js";

export default async function handler(req, res) {
  try {
    const byDay = await fetchContributionDays();
    const stats = computeStats(byDay);
    const svg = renderStreakSvg(stats);
    res.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
    res.setHeader(
      "Cache-Control",
      "public, max-age=60, s-maxage=60, stale-while-revalidate=30"
    );
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.status(200).send(svg);
  } catch (err) {
    res.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
    res.setHeader("Cache-Control", "no-store");
    res.status(500).send(errorSvg("Streak unavailable"));
  }
}
