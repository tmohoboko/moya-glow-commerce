// Existing IDs distinguish repeated names/categories without another catalogue.
export const serviceArtworkPath = product => `/catalogue/services/${product.id.normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}.svg`;
