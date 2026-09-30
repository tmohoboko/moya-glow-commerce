import {mkdir, readdir, readFile, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {products} from '../src/products.js';
import {serviceArtworkPath} from '../src/service-artwork.js';

const output = new URL('../public/catalogue/services/', import.meta.url);
if (products.length !== 46) throw new Error(`Expected 46 catalogue products; found ${products.length}. No assets written.`);
const paths = products.map(serviceArtworkPath);
if (new Set(paths).size !== 46) throw new Error('Duplicate service artwork slugs. No assets written.');
if (products.some((product, index) => product.image !== paths[index])) throw new Error('Catalogue artwork path mismatch.');
const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]));
function wrap(value, limit) {
  const lines = [''];
  for (const word of value.toUpperCase().split(/\s+/)) {
    const last = lines.length - 1;
    if (lines[last] && `${lines[last]} ${word}`.length > limit) lines.push(word);
    else lines[last] += `${lines[last] ? ' ' : ''}${word}`;
  }
  return lines;
}
function textLines(lines, y, size, step, family = 'Arial, sans-serif') {
  return lines.map((line, index) => `<text x="40" y="${y + index * step}" font-family="${family}" font-size="${size}">${escape(line)}</text>`).join('\n');
}
function artwork(product) {
  const names = wrap(product.name, 16);
  const categories = wrap(product.category, 32);
  const size = names.length > 2 ? 30 : 36;
  const duration = product.description.match(/\b(\d+)\s*min\b/i)?.[1];
  const price = `${product.priceFrom ? 'FROM ' : ''}R ${String(product.price).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 480 480" role="img" aria-labelledby="title">
<title id="title">${escape(`L Beauty · ${product.name} · ${product.category} · ${price}${duration ? ` · ${duration} MIN` : ''}`)}</title>
<rect width="480" height="480" fill="#f7f1e8"/>
<rect x="16" y="16" width="448" height="448" rx="4" fill="none" stroke="#b99b72"/>
<circle cx="411" cy="79" r="30" fill="none" stroke="#b99b72"/>
<path d="M389 82 Q411 39 433 82 Q411 109 389 82" fill="none" stroke="#b99b72"/>
<text x="40" y="77" font-family="Georgia, serif" font-size="30" letter-spacing="3" fill="#293e34">L BEAUTY</text>
<line x1="40" y1="111" x2="440" y2="111" stroke="#b99b72"/>
<g fill="#293e34">
${textLines(names, 181, size, 43, 'Georgia, serif')}
${textLines(categories, 329, 18, 25)}
<text x="40" y="410" font-family="Arial, sans-serif" font-size="30">${escape(price)}</text>
${duration ? `<text x="440" y="442" text-anchor="end" font-family="Arial, sans-serif" font-size="18">${duration} MIN</text>` : ''}
</g>
</svg>
`;
}
await mkdir(output, {recursive:true});
const expectedFiles = new Set(paths.map(path => path.split('/').at(-1)));
const unexpected = (await readdir(output)).filter(file => !expectedFiles.has(file));
if (unexpected.length) throw new Error(`Unexpected files in output directory: ${unexpected.join(', ')}. Review before generating.`);
for (const product of products) {
  const file = new URL(product.image.split('/').at(-1), output);
  const svg = artwork(product);
  await writeFile(file, svg);
  if (await readFile(file, 'utf8') !== svg) throw new Error(`Artwork verification failed: ${product.id}`);
}
const files = (await readdir(output)).filter(file => file.endsWith('.svg'));
if (files.length !== 46) throw new Error(`Expected 46 SVGs; found ${files.length}`);
console.log(`PASS: ${products.length} products / ${files.length} SVGs / ${new Set(paths).size} unique image paths`);
console.log(`Output: ${fileURLToPath(output)}`);
