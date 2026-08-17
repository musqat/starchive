import { expect, test } from "@playwright/test";

type Page = import("@playwright/test").Page;

const PASSWORD = "secret1234";

function newEmail() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

async function signUp(page: Page, nickname = "추천") {
  await page.goto("/signup");
  await page.getByPlaceholder("이메일").fill(newEmail());
  await page.getByPlaceholder("닉네임").fill(nickname);
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(PASSWORD);
  await page.getByRole("button", { name: "가입" }).click();
  await page.waitForURL("/");
}

test("비로그인이면 로그인 화면으로 보낸다", async ({ page }) => {
  await page.goto("/recommendations");

  await expect(page).toHaveURL(/\/login/);
});

test("기록이 없으면 매체마다 안내가 보인다", async ({ page }) => {
  await signUp(page);

  await page.goto("/recommendations");

  await expect(page.getByText("영화 5편을 평가하면")).toBeVisible();
  await expect(page.getByText("책 5편을 평가하면")).toBeVisible();
  // 만든 것이 없으면 만들었다고 쓰지 않는다
  await expect(page.getByText("평가를 함께 봤어요")).toHaveCount(0);
});

test("기록이 없으면 홈에 추천 줄이 없다", async ({ page }) => {
  await signUp(page, "추천홈");

  await expect(page.getByRole("heading", { name: "인기 영화" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "당신을 위한 영화" })).toHaveCount(0);
});

test("헤더의 추천으로 들어간다", async ({ page }) => {
  await signUp(page, "추천이동");

  await page.locator("header").getByRole("link", { name: "추천" }).click();

  await expect(page).toHaveURL("/recommendations");
  await expect(page.getByRole("heading", { name: "당신을 위한" })).toBeVisible();
});
