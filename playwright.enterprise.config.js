import {defineConfig} from '@playwright/test';
export default defineConfig({
  testDir:'./tests/playwright',outputDir:'test-results/enterprise',fullyParallel:false,workers:1,
  reporter:[['list'],['json',{outputFile:'qa/enterprise-results.json'}]],
  use:{baseURL:'http://127.0.0.1:8014',browserName:'chromium',launchOptions:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{},trace:'retain-on-failure'},
  webServer:{command:'PYTHONPATH=. .venv/bin/python scripts/enterprise-test-server.py',url:'http://127.0.0.1:8014/api/readiness',reuseExistingServer:false},
});
