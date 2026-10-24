// src/services/priceListService.js
// Service to load price list and provide price lookup by description (or SKU).
// Uses a Vite static JSON import so the file is bundled correctly in both dev
// and production builds (avoids the /src/data/... URL which only works in dev).

let _cache = null;

async function loadPriceList() {
  if (_cache) return _cache;
  // Vite resolves this import at build time and includes the JSON in the bundle.
  const mod = await import('../data/priceList.json');
  _cache = mod.default;
  return _cache;
}

/**
 * Find a price entry for a given description (case-insensitive substring match).
 * Returns the matching entry or null if not found.
 */
export async function findPriceByDescription(description) {
  const list = await loadPriceList();
  const lowered = description.toLowerCase();
  return list.find(item => item.description.toLowerCase().includes(lowered)) || null;
}

export { loadPriceList };
