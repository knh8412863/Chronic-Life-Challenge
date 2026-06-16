import { expect, test } from "@playwright/test";

test.describe("All4Health public smoke flow", () => {
  test("landing page loads and navigates to auth pages", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /생활습관 개선으로 시작하는 만성질환 관리/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "무료로 시작하기" }).first()).toBeVisible();

    await page.getByRole("button", { name: "무료로 시작하기" }).first().click();
    await expect(page).toHaveURL(/\/signup$/);
    await expect(page.getByRole("button", { name: /다음|회원가입|약관/ })).toBeVisible();

    await page.goto("/login");
    await expect(page.getByRole("button", { name: /로그인/ }).first()).toBeVisible();
    await expect(page.getByText(/비밀번호/).first()).toBeVisible();

    await page.goto("/password-reset");
    await expect(page.getByText(/비밀번호/).first()).toBeVisible();
  });

  test("service sections are reachable from landing page", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "서비스 둘러보기" }).first().click();
    await expect(page.getByRole("heading", { name: /AI가 함께하는 스마트 건강 관리/ })).toBeVisible();

    await expect(page.getByRole("heading", { name: "AI 건강 예측" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "5대 만성질환을 체계적으로 관리합니다" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "건강 챌린지로 습관을 바꾸세요" })).toBeVisible();
  });
});

test.describe("Optional deployed API smoke", () => {
  test.skip(!process.env.E2E_CHECK_API, "Set E2E_CHECK_API=1 to check deployed API docs response.");

  test("api docs endpoint responds", async ({ request }) => {
    const response = await request.get("/api/docs");
    expect([200, 405]).toContain(response.status());
  });
});
