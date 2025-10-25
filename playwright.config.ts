import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },

  use: {
    baseURL: 'http://localhost:3001',
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1280, height: 720 },
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...({ browserName: 'chromium' } as any) },
    },
    {
      name: 'firefox',
      use: { ...({ browserName: 'firefox' } as any) },
    },
    {
      name: 'webkit',
      use: { ...({ browserName: 'webkit' } as any) },
    },
  ],

  webServer: {
    command: 'npm run dev',
    port: 3001,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },

  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }]
  ],
})
