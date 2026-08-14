import { defineConfig, devices } from "@playwright/test";

/** 백엔드 FRONTEND_ORIGIN 이 이 주소 하나만 허용한다 */
const BASE_URL = "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // 같은 DB 를 쓰므로 순차 실행
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: "list",
  // 서버 컴포넌트가 API 와 DB 를 거쳐 렌더하므로 기본값(테스트 30초 / 단언 5초)으로는 모자란다
  timeout: 90_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  // 백엔드는 미리 실행해 둘 것 (cd backend && uv run uvicorn app.main:app)
  webServer: {
    command: "npm run dev",
    url: BASE_URL,
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
