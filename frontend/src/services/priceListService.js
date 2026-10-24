// src/services/priceListService.js
// Service to load price list and provide price lookup by description (or SKU)

export async function loadPriceList() {
  // In a real app this might fetch from an API; here we import the static JSON.
  const response = await fetch('/src/data/priceList.json');
  if (!response.ok) {
    throw new Error('Failed to load price list');
  }
  return response.json();
}

/**
 * Find price entry for a given description (case‑insensitive substring match).
 * Returns the matching entry or null if not found.
 */
export async function findPriceByDescription(description) {
  const list = await loadPriceList();
  const lowered = description.toLowerCase();
  const match = list.find(item => item.description.toLowerCase().includes(lowered));
  return match || null;
}
