const BASE = import.meta.env.VITE_API_URL || "";

export async function fetchTags() {
  const res = await fetch(`${BASE}/tags`);
  if (!res.ok) throw new Error("Failed to fetch tags");
  return res.json();
}

export async function fetchStickers({ tags = [], mode = "or", limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ mode, limit, offset });
  if (tags.length) params.set("tags", tags.join(","));
  const res = await fetch(`${BASE}/stickers?${params}`);
  if (!res.ok) throw new Error("Failed to fetch stickers");
  return res.json();
}

export async function fetchRandom({ tags = [], mode = "or" } = {}) {
  const params = new URLSearchParams({ mode });
  if (tags.length) params.set("tags", tags.join(","));
  const res = await fetch(`${BASE}/stickers/random?${params}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch random sticker");
  return res.json();
}
