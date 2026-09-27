import js from '@eslint/js';
import react from 'eslint-plugin-react';
import globals from 'globals';
export default [
  {ignores:['dist/**','node_modules/**','.deploy-enterprise/**','.venv/**','qa/**']},
  js.configs.recommended,
  {files:['**/*.{js,jsx}'],languageOptions:{ecmaVersion:'latest',sourceType:'module',parserOptions:{ecmaFeatures:{jsx:true}},globals:{...globals.browser,...globals.node}},plugins:{react},rules:{'react/jsx-uses-react':'error','react/jsx-uses-vars':'error','no-empty':['error',{allowEmptyCatch:true}]}},
];
