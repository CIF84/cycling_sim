import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";

test.use({ reducedMotion: "reduce" });

test("section shortcuts keep phone destinations visible, focused and usable after errors", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto("/?lang=cs");
  await expect(page.getByRole("status")).toContainText("Přehled aktualizován");
  const nav = page.getByRole("navigation", { name: "Části přehledu" });
  await nav
    .getByRole("link", { name: "Jídlo a pití", exact: true })
    .press("Enter");
  await expect(page.locator("#fuel-plan")).toBeFocused();
  const navBounds = await nav.boundingBox();
  const planBounds = await page.locator("#fuel-plan").boundingBox();
  expect(navBounds!.y).toBeGreaterThanOrEqual(0);
  expect(planBounds!.y).toBeGreaterThanOrEqual(
    navBounds!.y + navBounds!.height,
  );
  await page
    .getByRole("button", { name: "Sestavit plán", exact: true })
    .click();
  await nav.getByRole("link", { name: "Srovnání", exact: true }).click();
  await expect(page.locator("#comparisons")).toBeFocused();
  await nav.getByRole("link", { name: "Nastavení", exact: true }).click();
  await expect(page.locator("#ride-setup")).toBeFocused();
  await page.getByLabel("Hmotnost jezdce", { exact: true }).fill("0");
  await expect(page.getByRole("status")).toContainText("Zkontrolujte");
  await expect(
    nav.getByRole("link", { name: "Jídlo a pití", exact: true }),
  ).toBeDisabled();
  await expect(
    nav.getByRole("link", { name: "Srovnání", exact: true }),
  ).toBeDisabled();
  await nav.getByRole("link", { name: "Jízda", exact: true }).click();
  await expect(page.locator("#briefing")).toBeFocused();
  await page.getByRole("button", { name: "Obnovit výchozí nastavení" }).click();
  await expect(page.getByRole("status")).toContainText("Přehled aktualizován");
  await expect(
    nav.getByRole("link", { name: "Jídlo a pití", exact: true }),
  ).toBeEnabled();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("plan actions export the current plan, inspect timing and reject an invalid plan", async ({
  page,
}) => {
  await page.goto("/?lang=en");
  await expect(page.getByRole("status")).toContainText("Briefing updated");
  await page
    .getByRole("button", { name: "Build my plan", exact: true })
    .click();
  await page
    .getByLabel("Carbohydrate target", { exact: true })
    .selectOption("60");
  await page
    .getByRole("button", { name: "View timing on chart", exact: true })
    .click();
  await expect(page.locator("#ride-profile")).toBeFocused();
  await expect(page.getByTestId("profile-time")).toHaveText("10 min");
  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Save plan & briefing", exact: true })
    .click();
  const download = await downloadPromise;
  const text = await readFile((await download.path())!, "utf8");
  expect(text).toContain("86 g");
  expect(text).toContain("60 g/h");
  await page.getByLabel("Number of bottles", { exact: true }).fill("0");
  await expect(
    page.getByRole("button", { name: "Save plan & briefing", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "View timing on chart", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Download ride briefing", exact: true }),
  ).toBeEnabled();
});

test("action hierarchy stays labeled and accessible at desktop, tablet and narrow phone widths", async ({
  page,
}, testInfo) => {
  await page.goto("/?lang=cs");
  await expect(page.getByRole("status")).toContainText("Přehled aktualizován");
  await page.screenshot({
    path: `test-results/${testInfo.project.name}-ux-overview.png`,
    fullPage: false,
  });
  await page
    .getByRole("button", { name: "Sestavit plán", exact: true })
    .click();
  await page.getByRole("button", { name: "Energie", exact: true }).click();
  await page
    .locator("#ride-profile")
    .screenshot({ path: `test-results/${testInfo.project.name}-ux-chart.png` });
  await page
    .locator("#fuel-plan")
    .screenshot({ path: `test-results/${testInfo.project.name}-ux-plan.png` });
  for (const width of [768, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const save = page.getByRole("button", {
      name: "Stáhnout přehled jízdy",
      exact: true,
    });
    await expect(save.locator("span")).toBeVisible();
    expect((await save.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    const slider = page.getByLabel("Prozkoumat místo na trase", {
      exact: true,
    });
    expect((await slider.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  }
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(
    page.getByRole("button", { name: "Save plan & briefing", exact: true }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByRole("navigation", { name: "Ride sections" })
    .getByRole("link", { name: "Ride", exact: true })
    .click();
  await page.screenshot({
    path: `test-results/${testInfo.project.name}-ux-320.png`,
    fullPage: false,
  });
});
