import {clientOctoberPhotos} from './client-oct21.js';
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
  for (const photo of [...featuredPortfolioPhotos.filter(photo=>!photo.src.endsWith('portfolio-10.jpg')), ...clientOctoberPhotos, {id:'cat-eye-nail-art',src:'/catalogue/services/portfolio-10.jpg',label:'Cat eye nail finish',categories:['Cat eye'],collection:'Cat eye'}]) {
    const existing = result.get(photo.src);
    if(existing) {for(const category of photo.categories) if(!existing.categories.includes(category)) existing.categories.push(category)}
    else result.set(photo.src,{...photo,categories:[...photo.categories]});
  }
  return [...result.values()];
}
