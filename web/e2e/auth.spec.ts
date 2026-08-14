import { expect, test } from "@playwright/test";

type Page = import("@playwright/test").Page;

const PASSWORD = "secret1234";

function newEmail() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

/** 폼을 채우고 제출만 한다. 성공 여부는 호출하는 쪽에서 확인 */
async function submitSignUp(page: Page, email: string, nickname = "E2E") {
  await page.goto("/signup");
  await page.getByPlaceholder("이메일").fill(email);
  await page.getByPlaceholder("닉네임").fill(nickname);
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(PASSWORD);
  await page.getByRole("button", { name: "가입" }).click();
}

/** 가입 성공 후 홈으로 이동할 때까지 기다린다 */
async function signUp(page: Page, email: string, nickname = "E2E") {
  await submitSignUp(page, email, nickname);
  await page.waitForURL("/");
}

async function logOut(page: Page) {
  await page.getByRole("button", { name: "내 계정" }).click();

  // 이미 / 에 있어 waitForURL 은 즉시 통과한다. 전체 새로고침 자체를 기다려야 한다
  const reloaded = page.waitForEvent("load");
  await page.getByRole("menuitem", { name: "로그아웃" }).click();
  await reloaded;

  await expect(page.locator("header").getByRole("link", { name: "로그인" })).toBeVisible();
}

test("가입하면 헤더에 닉네임이 나온다", async ({ page }) => {
  await signUp(page, newEmail(), "가입테스터");

  await expect(page.locator("header")).toContainText("가입테스터");
});

test("로그아웃하면 헤더가 로그인으로 돌아온다", async ({ page }) => {
  await signUp(page, newEmail());

  await logOut(page);
});

test("로그아웃 후 다시 로그인된다", async ({ page }) => {
  const email = newEmail();
  await signUp(page, email, "재로그인");
  await logOut(page);

  await page.goto("/login");
  await page.getByPlaceholder("이메일").fill(email);
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(PASSWORD);
  await page.getByRole("button", { name: "로그인" }).click();
  await page.waitForURL("/");

  await expect(page.locator("header")).toContainText("재로그인");
});

test("같은 이메일로 두 번 가입하면 오류가 보인다", async ({ page }) => {
  const email = newEmail();
  await signUp(page, email);
  await logOut(page);

  await submitSignUp(page, email);

  await expect(page.getByText("Email already registered")).toBeVisible();
  await expect(page).toHaveURL("/signup");
});

test("비밀번호가 틀리면 오류가 보인다", async ({ page }) => {
  const email = newEmail();
  await signUp(page, email);
  await logOut(page);

  await page.goto("/login");
  await page.getByPlaceholder("이메일").fill(email);
  await page.getByPlaceholder("비밀번호", { exact: false }).fill("wrongpassword");
  await page.getByRole("button", { name: "로그인" }).click();

  await expect(page.getByText("invalid credentials")).toBeVisible();
});

test("새로고침해도 로그인이 유지된다", async ({ page }) => {
  await signUp(page, newEmail(), "유지테스터");

  await page.reload();

  await expect(page.locator("header")).toContainText("유지테스터");
});
