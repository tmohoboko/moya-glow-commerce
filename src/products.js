const groups = {
  Skincare: [['Gentle Cream Cleanser',149],['Hydrating Gel Cleanser',159],['Rosewater Toner',129],['Vitamin C Serum',249],['Hyaluronic Dew Serum',229],['Everyday Face Cream',199],['Nourishing Night Cream',239],['Mineral SPF 30 Lotion',259],['Clay Face Mask',179],['Soft Lip Balm',69]],
  Makeup: [['Skin Tint Foundation',279],['Cream Concealer',149],['Peach Cream Blush',169],['Golden Hour Highlighter',189],['Everyday Mascara',179],['Brow Defining Pencil',99],['Nude Rose Lipstick',139],['Clear Lip Gloss',109]],
  'Body care': [['Shea Body Butter',189],['Citrus Body Wash',129],['Vanilla Body Lotion',159],['Sugar Body Polish',179],['Soft Hands Cream',89],['Botanical Bath Soak',149]],
  'Hair care': [['Daily Gentle Shampoo',159],['Moisture Rich Conditioner',169],['Argan Hair Oil',199],['Deep Conditioning Mask',219],['Curl Defining Cream',179],['Leave-in Detangling Mist',149]]
};
export const products = Object.entries(groups).flatMap(([category, items]) => items.map(([name, price]) => ({id:name.toLowerCase().replaceAll(' ','-'),name,price,category,image:'/product.svg',description:`Make ${name.toLowerCase()} part of your everyday beauty ritual. A thoughtfully curated ${category.toLowerCase()} essential for your shelf. Mock product for the Moya Glow demo catalogue; packaging is illustrative.`})));
export const money = value => new Intl.NumberFormat('en-ZA',{style:'currency',currency:'ZAR'}).format(value);
