/** Shared GitHub GraphQL helpers for live profile SVGs. */

export const USERNAME = process.env.GITHUB_USERNAME || "shrey1110-dotcom";

export async function gql(query, variables = {}) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (!token) {
    throw new Error("GITHUB_TOKEN is required");
  }
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "User-Agent": "shrey1110-dotcom-profile-svgs",
    },
    body: JSON.stringify({ query, variables }),
  });
  const payload = await res.json();
  if (!res.ok || payload.errors) {
    throw new Error(JSON.stringify(payload.errors || payload));
  }
  return payload.data;
}

export function svgResponse(svg) {
  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      // Short cache so GitHub Camo / browsers revalidate often
      "Cache-Control": "public, max-age=60, s-maxage=60, stale-while-revalidate=30",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

export function errorSvg(message) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="495" height="120">
  <rect width="100%" height="100%" fill="#151515" rx="4"/>
  <text x="50%" y="50%" text-anchor="middle" fill="#f85149" font-family="Segoe UI, sans-serif" font-size="14">${message}</text>
</svg>`;
}
