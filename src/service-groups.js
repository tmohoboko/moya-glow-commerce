// Presentation groups preserve every authoritative service ID and price.
export const GROUPS = {
  'Nails': ['Gel & Acrylic Nail Enhancements', 'Others / Nails (Per Nail)', 'Natural Nails', 'Cat eye'],
  'Makeup': ['Makeup Looks'],
  'Lashes & Brows': ['Lash Extensions', 'Lash and Brow'],
  'Hands & Feet': ['Hand and Foot Treatments', 'Toes'],
  'Massage': ['Massage'],
  'Waxing': ['Body Wax', 'Facial Wax', 'Intimate Wax'],
};
export const serviceGroup = category => Object.keys(GROUPS).find(group => GROUPS[group].includes(category)) || category;
export const inGroup = (category, selected) => selected === 'All' || serviceGroup(category) === selected;
export function groupStats(services, photos) {
  return Object.keys(GROUPS).map(name => ({
    name,
    services:services.filter(service => serviceGroup(service.category) === name).length,
    pictures:new Set(photos.filter(photo => photo.categories.some(category => serviceGroup(category) === name)).map(photo => photo.src)).size,
  })).sort((a,b) => a.name === 'Waxing' ? 1 : b.name === 'Waxing' ? -1 : b.pictures-a.pictures || a.name.localeCompare(b.name));
}
export function orderedServices(services, groups) {
  const rank = new Map(groups.map((group,i) => [group.name,i]));
  return [...services].sort((a,b) => rank.get(serviceGroup(a.category))-rank.get(serviceGroup(b.category)));
}
