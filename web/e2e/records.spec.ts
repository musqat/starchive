import { expect, test } from "@playwright/test";

type Page = import("@playwright/test").Page;

const PASSWORD = "secret1234";
const TITLE = "인터스텔라";
const DETAIL = "/contents/tmdb_157336";

function newEmail() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

async function signUp(page: Page) {
  await page.goto("/signup");
  await page.getByPlaceholder("이메일").fill(newEmail());
  await page.getByPlaceholder("닉네임").fill("기록");
  await page.getByPlaceholder("비밀번호", { exact: false }).fill(PASSWORD);
  await page.getByRole("button", { name: "가입" }).click();
  await page.waitForURL("/");
}

/** 카드 버튼은 제목이 붙은 aria-label 로 구분한다 */
const card = (page: Page, name: string) =>
  page.getByRole("button", { name: `${TITLE} ${name}` });

/** 상세 버튼은 아이콘이 앞에 붙어 부분 일치로 찾는다 */
const detail = (page: Page, name: string) =>
  page.getByRole("button", { name, exact: false });

const star = (page: Page, n: number) => page.getByRole("button", { name: `${n}점` });
const cardStar = (page: Page, n: number) => card(page, `${n}점`);

/** 낙관적 갱신이라 화면만 보면 저장 완료를 알 수 없다. 응답까지 기다린다 */
async function saving(page: Page, action: Promise<void>) {
  const saved = page.waitForResponse(
    (r) => /\/me\/records\//.test(r.url()) && r.request().method() !== "OPTIONS",
  );
  await action;
  await saved;
}

test("비로그인은 눌러도 저장되지 않는다는 안내가 뜬다", async ({ page }) => {
  await page.goto("/movies");
  await card(page, "봤어요").click();

  await expect(page.getByText("기록은 저장되지 않습니다")).toBeVisible();
});

test("봤어요를 켜야 별점이 나타난다", async ({ page }) => {
  await signUp(page);
  await page.goto("/movies");

  await expect(cardStar(page, 3)).toHaveCount(0);

  await card(page, "봤어요").click();

  await expect(cardStar(page, 3)).toBeVisible();
});

test("기록이 새로고침 후에도 남는다", async ({ page }) => {
  await signUp(page);
  await page.goto("/movies");

  await saving(page, card(page, "봤어요").click());
  await saving(page, cardStar(page, 3).click());

  await page.reload();

  await expect(card(page, "봤어요")).toHaveAttribute("aria-pressed", "true");
  await expect(cardStar(page, 3)).toHaveAttribute("aria-pressed", "true");
});

test("봤어요를 끄면 기록이 사라진다", async ({ page }) => {
  await signUp(page);
  await page.goto("/movies");

  await saving(page, card(page, "봤어요").click());
  await saving(page, card(page, "봤어요").click());
  await expect(cardStar(page, 3)).toHaveCount(0);

  await page.goto("/library");
  await expect(page.getByText("아직 기록이 없습니다")).toBeVisible();
});

test("기록한 항목이 보관함에 나온다", async ({ page }) => {
  await signUp(page);
  await page.goto("/movies");
  await saving(page, card(page, "봤어요").click());

  await page.goto("/library");

  await expect(page.locator("main")).toContainText(TITLE);
});

test("상세에서 별점을 매기면 봤어요도 켜진다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  await saving(page, star(page, 4).click());

  await expect(star(page, 4)).toHaveAttribute("aria-pressed", "true");
  await expect(detail(page, "봤어요")).toHaveAttribute("aria-pressed", "true");

  await page.reload();
  await expect(star(page, 4)).toHaveAttribute("aria-pressed", "true");
});

test("같은 별을 다시 누르면 평점이 지워진다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  await saving(page, star(page, 3).click());
  await saving(page, star(page, 3).click());

  await page.reload();

  await expect(star(page, 3)).toHaveAttribute("aria-pressed", "false");
  await expect(detail(page, "봤어요")).toHaveAttribute("aria-pressed", "true");
});

test("안 본 것만 켜면 기록한 항목이 목록에서 빠진다", async ({ page }) => {
  await signUp(page);
  await page.goto("/movies");

  const count = page.locator("main").getByText(/편$/);
  const before = await count.textContent();

  await saving(page, card(page, "봤어요").click());
  await page.getByRole("link", { name: "안 본 것만" }).click();

  await expect(page).toHaveURL(/unseen=1/);
  await expect(card(page, "봤어요")).toHaveCount(0);
  await expect(count).not.toHaveText(before ?? "");
});

test("비로그인은 안 본 것만 칩이 없다", async ({ page }) => {
  await page.goto("/movies");

  await expect(page.getByRole("link", { name: "안 본 것만" })).toHaveCount(0);
});

test("상세에서 좋아요와 추천해요는 따로 켜진다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  await saving(page, detail(page, "봤어요").click());
  await saving(page, detail(page, "좋아요").click());

  await page.reload();

  await expect(detail(page, "좋아요")).toHaveAttribute("aria-pressed", "true");
  await expect(detail(page, "추천해요")).toHaveAttribute("aria-pressed", "false");
});

test("댓글을 남기면 새로고침 후에도 남는다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  const memo = page.getByLabel("내 댓글");
  await memo.fill("다시 볼 것");
  await saving(page, page.getByRole("button", { name: "저장" }).click());

  await expect(page.getByText("저장했습니다")).toBeVisible();

  await page.reload();
  await expect(memo).toHaveValue("다시 볼 것");
});

test("공개하지 않은 댓글은 남에게 보이지 않는다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  await page.getByLabel("내 댓글").fill("혼자만 볼 것");
  await saving(page, page.getByRole("button", { name: "저장" }).click());

  // 다른 계정으로 바꿔 본다
  await page.getByRole("button", { name: "내 계정" }).click();
  await page.getByRole("menuitem", { name: "로그아웃" }).click();
  await page.waitForURL("/");
  await signUp(page);
  await page.goto(DETAIL);

  await expect(page.locator("main")).not.toContainText("혼자만 볼 것");
});

test("댓글 탭에 댓글 남긴 것만 본문과 함께 나온다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  await page.getByLabel("내 댓글").fill("탭에서 보일 것");
  await saving(page, page.getByRole("button", { name: "저장" }).click());

  await page.goto("/library?filter=memo");

  await expect(page.locator("main")).toContainText(TITLE);
  await expect(page.locator("main")).toContainText("탭에서 보일 것");
});

test("댓글을 고치고 지울 수 있다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  const memo = page.getByLabel("내 댓글");
  const save = page.getByRole("button", { name: "저장" });
  const remove = page.getByRole("button", { name: "삭제" });

  // 메모가 없으면 삭제 버튼도 없다
  await expect(remove).toHaveCount(0);

  await memo.fill("처음 쓴 것");
  await saving(page, save.click());
  await expect(remove).toBeVisible();

  await memo.fill("고쳐 쓴 것");
  await saving(page, save.click());
  await page.reload();
  await expect(memo).toHaveValue("고쳐 쓴 것");

  await saving(page, remove.click());
  await expect(page.getByText("지웠습니다")).toBeVisible();

  await page.reload();
  await expect(memo).toHaveValue("");
  await expect(remove).toHaveCount(0);
});

test("저장하지 않은 댓글이 있으면 드로어가 바로 닫히지 않는다", async ({ page }) => {
  await signUp(page);
  await page.goto("/movies");
  await page.locator('a[href^="/contents/"]').first().click();

  const drawer = page.getByRole("dialog");
  await expect(drawer).toBeVisible();
  await page.getByLabel("내 댓글").fill("한참 쓰던 댓글");

  // 취소하면 그대로 남는다
  page.once("dialog", (d) => d.dismiss());
  await drawer.click({ position: { x: 20, y: 300 } });
  await expect(drawer).toBeVisible();
  await expect(page.getByLabel("내 댓글")).toHaveValue("한참 쓰던 댓글");

  // 저장하면 묻지 않고 닫힌다
  await saving(page, page.getByRole("button", { name: "저장" }).click());
  await drawer.click({ position: { x: 20, y: 300 } });
  await expect(drawer).toHaveCount(0);
});

test("내용 없이 공개만 켜서 저장할 수 없다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  const publish = page.getByRole("checkbox", { name: "공개" });
  const save = page.getByRole("button", { name: "저장" });

  await expect(publish).toBeDisabled();
  await expect(save).toBeDisabled();

  await page.getByLabel("내 댓글").fill("이제 쓴다");
  await expect(publish).toBeEnabled();
  await expect(save).toBeEnabled();

  // 저장하고 나면 다시 잠긴다
  await saving(page, save.click());
  await expect(save).toBeDisabled();
});

test("상세에서 0.5 단위로 평점을 매긴다", async ({ page }) => {
  await signUp(page);
  await page.goto(DETAIL);

  await saving(page, star(page, 3.5).click());
  await expect(star(page, 3.5)).toHaveAttribute("aria-pressed", "true");

  await page.reload();
  await expect(star(page, 3.5)).toHaveAttribute("aria-pressed", "true");
  await expect(star(page, 4)).toHaveAttribute("aria-pressed", "false");
});
