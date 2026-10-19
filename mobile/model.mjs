export function distanceMetres(origin, facility) {
  if (![origin.x, origin.y, facility.x, facility.y].every(Number.isFinite)) {
    throw new Error('Invalid projected metre coordinates');
  }
  return Math.hypot(origin.x - facility.x, origin.y - facility.y);
}

export function selectFacilities(pack, {category = 'all', query = '', savedOnly = false, saved = []} = {}) {
  return pack.facilities
    .filter(f => (category === 'all' || f.category === category)
      && f.name.toLowerCase().includes(query.trim().toLowerCase())
      && (!savedOnly || saved.includes(f.id)))
    .map(f => ({...f, distance: distanceMetres(pack.origin, f)}))
    .sort((a,b) => a.distance - b.distance || a.id.localeCompare(b.id));
}

export function parseSaved(value, facilities) {
  const parsed = JSON.parse(value || '[]');
  if (!Array.isArray(parsed)) throw new Error('Invalid saved places');
  return [...new Set(parsed.filter(id => typeof id === 'string' && facilities.some(f => f.id === id)))];
}
