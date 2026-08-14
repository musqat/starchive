import { expect, test } from "@playwright/test";

type Page = import("@playwright/test").Page;

const PASSWORD = "secret1234";

function newEmail() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

async function signUp(page: Page, nickname = "서재") {
  await page.goto("/signup");
  await page.getByPlaceholder("이메일").fill(newEmail());
  await page.getByPlaceholder("닉네임").fill(nickname);
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(PASSWORD);
  await page.getByRole("button", { name: "가입" }).click();
  await page.waitForURL("/");
}

test("비로그인이면 로그인 화면으로 보낸다", async ({ page }) => {
  await page.goto("/library");

  await expect(page).toHaveURL("/login");
});

test("기록이 없으면 빈 상태가 보인다", async ({ page }) => {
  await signUp(page);

  await page.goto("/library");

  await expect(page.getByText("아직 기록이 없습니다")).toBeVisible();
});

test("헤더의 보관함으로 들어간다", async ({ page }) => {
  await signUp(page, "서재이동");

  await page.locator("header").getByRole("link", { name: "보관함" }).click();

  await expect(page).toHaveURL("/library");
  await expect(page.getByRole("heading", { name: "보관함" })).toBeVisible();
});

test("기록을 남기면 서재에 나오고 상태 탭으로 걸러진다", async ({ page }) => {
  await signUp(page);

  // 카드 토글 UI 는 아직 없어서 API 로 직접 남긴다
  const put = (id: string, body: object) =>
    page.evaluate(
      ([contentId, payload]) =>
        fetch(`http://localhost:8000/me/records/${contentId}`, {
          method: "PUT",
          credentials: "include",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        }).then((r) => r.status),
      [id, body] as const,
    );

  expect(await put("tmdb_157336", { status: "WISH" })).toBe(200);
  expect(await put("aladin_9788937460586", { recommended: true })).toBe(200);

  await page.goto("/library");
  await expect(page.locator("main")).toContainText("인터스텔라");
  await expect(page.locator("main")).toContainText("싯다르타");

  // 이동이 끝나기 전에 단언하면 직전 목록을 보게 된다
  await page.getByRole("link", { name: "보고싶어요" }).click();
  await page.waitForURL("/library?status=WISH");
  await expect(page.locator("main")).toContainText("인터스텔라");
  await expect(page.locator("main")).not.toContainText("싯다르타");

  await page.getByRole("link", { name: "봤어요" }).click();
  await page.waitForURL("/library?status=DONE");
  await expect(page.locator("main")).toContainText("싯다르타");
  await expect(page.locator("main")).not.toContainText("인터스텔라");
});
