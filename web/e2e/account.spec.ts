import { expect, test } from "@playwright/test";

type Page = import("@playwright/test").Page;

const PASSWORD = "secret1234";
const NEXT_PASSWORD = "newsecret1234";

function newEmail() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

async function signUp(page: Page) {
  const email = newEmail();
  await page.goto("/signup");
  await page.getByPlaceholder("이메일").fill(email);
  await page.getByPlaceholder("닉네임").fill("계정");
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(PASSWORD);
  await page.getByRole("button", { name: "가입" }).click();
  await page.waitForURL("/");
  return email;
}

test("비로그인이면 로그인 화면으로 보낸다", async ({ page }) => {
  await page.goto("/account");
  await expect(page).toHaveURL(/\/login/);
});

test("드롭다운에서 마이페이지로 간다", async ({ page }) => {
  await signUp(page);
  await page.getByRole("button", { name: "내 계정" }).click();
  await page.getByRole("menuitem", { name: "마이페이지" }).click();

  await expect(page).toHaveURL("/account");
  await expect(page.getByRole("heading", { name: "계정" })).toBeVisible();
});

test("비밀번호를 바꾸면 새 비밀번호로 로그인된다", async ({ page }) => {
  const email = await signUp(page);
  await page.goto("/account");

  await page.getByPlaceholder("현재 비밀번호").fill(PASSWORD);
  await page.getByPlaceholder("새 비밀번호", { exact: false }).fill(NEXT_PASSWORD);
  await page.getByRole("button", { name: "변경" }).click();
  await expect(page.getByText("비밀번호를 바꿨습니다")).toBeVisible();

  await page.getByRole("button", { name: "내 계정" }).click();
  await page.getByRole("menuitem", { name: "로그아웃" }).click();
  await page.waitForURL("/");

  await page.goto("/login");
  await page.getByPlaceholder("이메일").fill(email);
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(NEXT_PASSWORD);
  await page.getByRole("button", { name: "로그인" }).click();

  await expect(page.getByRole("button", { name: "내 계정" })).toBeVisible();
});

test("현재 비밀번호가 틀리면 알린다", async ({ page }) => {
  await signUp(page);
  await page.goto("/account");

  await page.getByPlaceholder("현재 비밀번호").fill("wrongpassword");
  await page.getByPlaceholder("새 비밀번호", { exact: false }).fill(NEXT_PASSWORD);
  await page.getByRole("button", { name: "변경" }).click();

  await expect(page.getByRole("alert")).toBeVisible();
});

test("탈퇴하면 계정이 사라진다", async ({ page }) => {
  const email = await signUp(page);
  await page.goto("/account");

  await page.getByRole("button", { name: "탈퇴하기" }).click();
  await page.getByPlaceholder("비밀번호", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: "탈퇴", exact: true }).click();
  await page.waitForURL("/");

  await page.goto("/login");
  await page.getByPlaceholder("이메일").fill(email);
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(PASSWORD);
  await page.getByRole("button", { name: "로그인" }).click();

  await expect(page.getByRole("alert")).toBeVisible();
});
