import {featuredPortfolioPhotos} from './photo-library.js';
// One distinct image per source. Every displayed photo belongs to actual
// treatments, so generic category-room imagery cannot dilute the catalogue.
export function serviceGallery(services) {
  const result = new Map();
  for (const service of services) {
    const existing = result.get(service.image);
    if(existing) {if(!existing.categories.includes(service.category)) existing.categories.push(service.category)}
    else result.set(service.image,{id:service.id,src:service.image,label:service.name,categories:[service.category]});
  }
  for (const photo of featuredPortfolioPhotos) {
    const existing = result.get(photo.src);
    if(existing) {for(const category of photo.categories) if(!existing.categories.includes(category)) existing.categories.push(category)}
    else result.set(photo.src,{...photo,categories:[...photo.categories]});
  }
  return [...result.values()];
}
