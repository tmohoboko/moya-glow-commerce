import {servicePhotoUpdates} from './service-photo-updates.js';
// Photos are representative portfolio examples; IDs and prices remain authoritative.
const supplied = number => `/catalogue/services/portfolio-${String(number).padStart(2, '0')}.jpg`;
const illustration = slug => `/catalogue/services/illustrative-${slug}.jpg`;
const servicePhotos = {
  'intimate-wax-hollywood-260': '/catalogue/services/focus-intimate-wax.jpg',
  'makeup-looks-classic-nude-natural-350': '/catalogue/services/makeup-classic-nude-natural.jpg',
  'makeup-looks-full-glam-400': '/catalogue/services/makeup-full-glam.jpg',
  'makeup-looks-bridal-1000': supplied(15),
  'makeup-looks-special-effects-600': illustration('special-effects'),
  'gel-acrylic-nail-enhancements-gel-overlay-1-any-colour-120': supplied(7),
  'gel-acrylic-nail-enhancements-tips-any-length-200': supplied(30),
  'nails-french-250': supplied(29),
  'gel-acrylic-nail-enhancements-acrylic-overlay-1-any-colour-150': supplied(10),
  'gel-acrylic-nail-enhancements-tips-any-size-230': supplied(28),
  'nails-french-280': supplied(24),
  'others-nails-per-nail-art-per-nail-5': supplied(11),
  'others-nails-per-nail-chrome-2': supplied(25),
  'others-nails-per-nail-charms-rhinestones-7': supplied(4),
  'others-nails-per-nail-3d-10': supplied(5),
  'hand-and-foot-treatments-full-manicure-200': supplied(2),
};
export const categoryPhotos = {
  'Massage': illustration('massage'),
  'Hand and Foot Treatments': illustration('hand-foot'),
  'Body Wax': illustration('body-wax'),
  'Intimate Wax': illustration('intimate-wax'),
  'Facial Wax': illustration('facial-wax'),
  'Lash Extensions': illustration('lash-extensions'),
  'Lash and Brow': illustration('lash-brow'),
  'Toes': illustration('toes'),
};
export const serviceArtworkPath = product => servicePhotoUpdates[product.id] ?? servicePhotos[product.id] ?? categoryPhotos[product.category] ?? `/catalogue/services/${product.id.normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}.svg`;
const categoryInspiration = [
  ...Object.entries(categoryPhotos).map(([category,src]) => ({id:category,src,label:category,categories:[category],source:'Service inspiration'})),
  {id:'special-effects',src:illustration('special-effects'),label:'Special Effects makeup',categories:['Makeup Looks'],source:'Service inspiration'},
];

export const galleryInspiration = products => [...categoryInspiration,...Object.entries(servicePhotoUpdates).map(([id,src])=>{const product=products.find(p=>p.id===id);return {id,src,label:product.name,categories:[product.category],source:'Service inspiration'};})];
