import React from 'react';

// Layout-only framing: keep the original photographs intact and focus on the
// treatment. All framed sources are square 1254px images; rectangles stay square
// to preserve anatomy/proportions. No image pixel data is modified.
const crops = {
  'service-back-wax.jpg': [0.10,0.34,0.65],
  'service-full-body.jpg': [0.48,0.36,0.38],
  'illustrative-massage.jpg': [0.26,0.45,0.28],
  'service-aromatherapy.jpg': [0.23,0.42,0.45],
  'service-full-pedicure.jpg': [0.20,0.44,0.42],
  'service-full-arm-wax.jpg': [0.39,0.50,0.43],
  'service-underarm-care.jpg': [0.58,0.35,0.30],
  'illustrative-facial-wax.jpg': [0.21,0.25,0.53],
  'service-face-wax-combo.jpg': [0.39,0.27,0.43],
  'service-full-face-wax.jpg': [0.39,0.26,0.43],
  'service-classic-lashes.jpg': [0.27,0.30,0.30],
  'service-hybrid-lashes.jpg': [0.42,0.23,0.21],
  'illustrative-lash-extensions.jpg': [0.28,0.34,0.34],
  'service-cluster-lashes.jpg': [0.22,0.04,0.35],
  'service-cat-eye-lashes.jpg': [0.30,0.22,0.30],
  'illustrative-lash-brow.jpg': [0.35,0.22,0.35],
  'service-lash-tint.jpg': [0.32,0.24,0.30],
  'service-lash-brow-combo.jpg': [0.33,0.30,0.22],
  'service-brow-shaping.jpg': [0.36,0.29,0.32],
};
export function imageCrop(src) {return crops[src.split('/').pop()] || null}
export function TreatmentImage({src,alt,loading,style,className = ''}) {
  const client = src.includes('/client-oct21/');
  const rotation = /client-(08|09|11)\.jpg$/.test(src)?90:/client-10\.jpg$/.test(src)?180:0;
  const crop = imageCrop(src);
  const frame = crop ? {'--photo-width':`${100/crop[2]}%`,'--photo-left':`${-crop[0]*100/crop[2]}%`,'--photo-top':`${-crop[1]*100/crop[2]}%`} : {};
  return <span className={`treatment-photo ${crop ? 'treatment-photo--focused' : ''} ${client ? `client-treatment-photo client-treatment-photo--${rotation} client-treatment-photo--${src.split('/').pop().replace('.jpg','')}` : ''} ${className}`} style={frame} data-focused={Boolean(crop)}><img src={src} alt={alt} loading={loading} style={crop ? undefined : style}/></span>;
}
