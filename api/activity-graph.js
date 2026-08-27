import { errorSvg } from "../lib/github.js";
import { fetchRecentDays, renderActivitySvg } from "../lib/activity.js";

export default async function handler(req, res) {
  try {
    const days = await fetchRecentDays();
    const svg = renderActivitySvg(days);
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
    res.status(500).send(errorSvg("Activity graph unavailable"));
  }
}
