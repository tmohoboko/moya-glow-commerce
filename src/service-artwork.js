// Existing IDs distinguish repeated names/categories without another catalogue.
const servicePhotos = {
  'makeup-looks-classic-nude-natural-350': '/catalogue/services/makeup-classic-nude-natural.jpg',
  'makeup-looks-full-glam-400': '/catalogue/services/makeup-full-glam.jpg',
};
export const serviceArtworkPath = product => servicePhotos[product.id] ?? `/catalogue/services/${product.id.normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}.svg`;
