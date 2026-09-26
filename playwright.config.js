import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',reporter:[['list'],['json',{outputFile:'qa/smoke-results.json'}]],use:{baseURL:process.env.BASE_URL||'http://127.0.0.1:4173',browserName:'chromium'},webServer:process.env.BASE_URL?undefined:{command:'npm run preview -- --port 4173',url:'http://127.0.0.1:4173',reuseExistingServer:false}});
