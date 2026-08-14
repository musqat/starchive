import { expect, test } from "@playwright/test";

test("대시보드에 영화와 책 캐러셀이 나온다", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "인기 영화" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "인기 책" })).toBeVisible();
  await expect(page.locator("img").first()).toBeVisible();
});

test("영화 목록에서 장르로 거를 수 있다", async ({ page }) => {
  await page.goto("/movies");
  await page.getByRole("link", { name: "SF", exact: true }).click();

  await expect(page).toHaveURL(/genre=SF/);
  await expect(page.locator("main")).toContainText("영화");
});

test("정렬을 다시 누르면 방향이 뒤집힌다", async ({ page }) => {
  await page.goto("/movies");
  await page.getByRole("link", { name: /평점순/ }).click();
  await expect(page).toHaveURL(/sort=rating/);

  await page.getByRole("link", { name: /평점순/ }).click();
  await expect(page).toHaveURL(/order=asc/);
});

test("검색하면 결과가 타입별로 묶여 나온다", async ({ page }) => {
  await page.goto("/");
  await page.getByPlaceholder("제목 검색").fill("반지의");
  await page.getByRole("button", { name: "검색" }).click();

  await expect(page).toHaveURL(/\/search/);
  await expect(page.locator("main")).toContainText("반지의 제왕");
});

test("카드를 누르면 드로어가 열리고 배경을 누르면 닫힌다", async ({ page }) => {
  await page.goto("/movies");
  await page.locator('a[href^="/contents/"]').first().click();

  const drawer = page.getByRole("dialog");
  await expect(drawer).toBeVisible();

  await page.getByRole("button", { name: "닫기" }).click();
  await expect(drawer).toBeHidden();
});

test("상세 URL 로 직접 들어가면 전체 페이지가 나온다", async ({ page }) => {
  await page.goto("/contents/tmdb_157336");

  await expect(page.getByRole("heading", { name: "인터스텔라" })).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("없는 콘텐츠는 404", async ({ page }) => {
  const res = await page.goto("/contents/does-not-exist");

  expect(res?.status()).toBe(404);
});

test("드로어에서 페이지로 열 수 있다", async ({ page }) => {
  await page.goto("/movies");
  await page.locator('a[href^="/contents/"]').first().click();
  await expect(page.getByRole("dialog")).toBeVisible();

  await page.getByRole("link", { name: "페이지로 열기" }).click();

  await expect(page).toHaveURL(/\/contents\//);
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("영화 상세에 볼 수 있는 곳이 나온다", async ({ page }) => {
  await page.goto("/contents/tmdb_157336");

  await expect(page.getByText("볼 수 있는 곳")).toBeVisible();
  await expect(page.getByRole("link", { name: "보러 가기" })).toBeVisible();
});

test("책 상세에 알라딘 링크가 나온다", async ({ page }) => {
  await page.goto("/contents/aladin_9788937460586");

  const link = page.getByRole("link", { name: /알라딘에서 보기/ });
  await expect(link).toHaveAttribute("href", /aladin\.co\.kr/);
});
