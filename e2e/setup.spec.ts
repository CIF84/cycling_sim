import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";

const key = "bike-science-setup";
const ready = (page: Page, cs = false) =>
  expect(page.getByRole("status")).toContainText(
    cs ? "Přehled aktualizován" : "Briefing updated",
  );
const remember = (page: Page) =>
  page.getByRole("checkbox", {
    name: "Remember my setup on this device",
    exact: true,
  });
const stored = (page: Page) =>
  page.evaluate((k) => localStorage.getItem(k), key);
const gearing = (page: Page) =>
  page.locator("summary").filter({ hasText: "Gearing & cadence" }).click();
const conditions = (page: Page) =>
  page.locator("summary").filter({ hasText: "Conditions & model" }).click();

test("opt-in restores rider and preset preferences, but never GPX or visit conditions", async ({
  page,
}) => {
  await page.goto("/?lang=en");
  await ready(page);
  await expect(remember(page)).not.toBeChecked();
  await page.getByLabel("Rider weight", { exact: true }).fill("81.5");
  await ready(page);
  expect(await stored(page)).toBeNull();
  await page.reload();
  await ready(page);
  await expect(page.getByLabel("Rider weight", { exact: true })).toHaveValue(
    "75",
  );
  await page.getByLabel("Rider weight", { exact: true }).fill("81.5");
  await page.getByLabel("Sustainable power", { exact: true }).fill("215");
  await page
    .getByLabel("Surface & tires", { exact: false })
    .selectOption("0.008");
  await gearing(page);
  await page
    .getByLabel("Groupset preset", { exact: true })
    .selectOption("shimano-grx-rx820-1x51");
  await page.getByLabel("Preferred cadence", { exact: true }).fill("90");
  await conditions(page);
  await page.getByLabel("Along-route wind", { exact: true }).fill("8");
  await page.getByLabel("Temperature", { exact: true }).fill("30");
  await page.getByLabel("Air-density altitude", { exact: true }).fill("900");
  await page.getByLabel("Speed ceiling", { exact: true }).fill("45");
  await page
    .locator("#gpx-file")
    .setInputFiles(path.resolve("e2e/fixtures/synthetic.gpx"));
  await ready(page);
  await remember(page).check();
  await expect(page.locator("#remember-status")).toContainText("Saved here");
  const saved = JSON.parse((await stored(page))!);
  expect(saved.inputs).toMatchObject({
    riderKg: 81.5,
    powerW: 215,
    crr: 0.008,
    cadenceRpm: 90,
    speedLimitKmh: 45,
  });
  expect(await stored(page)).not.toMatch(
    /rolling|trkpt|xml|wind|temperature|altitude/,
  );
  await page.reload();
  await ready(page);
  await expect(remember(page)).toBeChecked();
  await expect(
    page.getByRole("heading", { name: "The Sunday Loop", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Rider weight", { exact: true })).toHaveValue(
    "81.5",
  );
  await expect(
    page.getByLabel("Sustainable power", { exact: true }),
  ).toHaveValue("215");
  await gearing(page);
  await expect(page.getByLabel("Groupset preset", { exact: true })).toHaveValue(
    "shimano-grx-rx820-1x51",
  );
  await expect(
    page.getByLabel("Front chainrings", { exact: true }),
  ).toHaveValue("40");
  await conditions(page);
  await expect(
    page.getByLabel("Along-route wind", { exact: true }),
  ).toHaveValue("0");
  await expect(page.getByLabel("Temperature", { exact: true })).toHaveValue(
    "20",
  );
  await expect(
    page.getByLabel("Air-density altitude", { exact: true }),
  ).toHaveValue("200");
  await expect(page.getByLabel("Speed ceiling", { exact: true })).toHaveValue(
    "45",
  );
});

test("custom gearing persists, invalid edits keep the last valid setup, and reset saves defaults", async ({
  page,
}) => {
  await page.goto("/?lang=en");
  await ready(page);
  await remember(page).check();
  await gearing(page);
  await page.getByLabel("Front chainrings", { exact: true }).fill("30, 46");
  await page.getByLabel("Front chainrings", { exact: true }).press("Tab");
  await page
    .getByLabel("Cassette cogs", { exact: true })
    .fill("11, 13, 17, 24, 36");
  await page.getByLabel("Cassette cogs", { exact: true }).press("Tab");
  await page.getByLabel("Sustainable power", { exact: true }).fill("205");
  await ready(page);
  await page.getByLabel("Sustainable power", { exact: true }).fill("");
  await expect(page.locator("#remember-status")).toContainText(
    "aren’t saved yet",
  );
  expect(JSON.parse((await stored(page))!).inputs.powerW).toBe(205);
  await page.reload();
  await ready(page);
  await expect(
    page.getByLabel("Sustainable power", { exact: true }),
  ).toHaveValue("205");
  await gearing(page);
  await expect(page.getByLabel("Groupset preset", { exact: true })).toHaveValue(
    "custom",
  );
  await expect(
    page.getByLabel("Front chainrings", { exact: true }),
  ).toHaveValue("30, 46");
  await expect(page.getByLabel("Cassette cogs", { exact: true })).toHaveValue(
    "11, 13, 17, 24, 36",
  );
  await page
    .getByRole("button", { name: "Reset ride inputs", exact: true })
    .click();
  await ready(page);
  await page.reload();
  await ready(page);
  await expect(remember(page)).toBeChecked();
  await expect(
    page.getByLabel("Sustainable power", { exact: true }),
  ).toHaveValue("180");
  await gearing(page);
  await expect(page.getByLabel("Groupset preset", { exact: true })).toHaveValue(
    "shimano-105-r7100",
  );
});

test("forget keeps current inputs and language, and stops other tabs from saving again", async ({
  page,
  context,
}) => {
  await page.goto("/?lang=en");
  await ready(page);
  await page.getByLabel("Sustainable power", { exact: true }).fill("210");
  await remember(page).check();
  await expect(page.locator("#remember-status")).toContainText("Saved here");
  const second = await context.newPage();
  await second.goto("/?lang=en");
  await ready(second);
  await expect(remember(second)).toBeChecked();
  await remember(page).uncheck();
  await expect(page.locator("#remember-status")).toContainText(
    "Saved setup removed",
  );
  await expect(
    page.getByLabel("Sustainable power", { exact: true }),
  ).toHaveValue("210");
  await expect(remember(second)).not.toBeChecked();
  await second.getByLabel("Sustainable power", { exact: true }).fill("220");
  await ready(second);
  expect(await stored(second)).toBeNull();
  expect(
    await page.evaluate(() => localStorage.getItem("bike-science-language")),
  ).toBe("en");
  await page.reload();
  await ready(page);
  await expect(remember(page)).not.toBeChecked();
  await expect(
    page.getByLabel("Sustainable power", { exact: true }),
  ).toHaveValue("180");
  await second.close();
});

test("corrupt storage recovers and Czech saved state stays accessible at narrow widths", async ({
  page,
}, info) => {
  await page.addInitScript(
    (k) => localStorage.setItem(k, '{"version":999}'),
    key,
  );
  await page.goto("/?lang=cs");
  await ready(page, true);
  await expect(page.locator("#remember-status")).toContainText(
    "nepodařilo načíst",
  );
  const checkbox = page.getByRole("checkbox", {
    name: "Zapamatovat nastavení v tomto zařízení",
    exact: true,
  });
  await expect(checkbox).not.toBeChecked();
  await page.getByLabel("Hmotnost jezdce", { exact: true }).fill("82,5");
  await checkbox.check();
  await expect(page.locator("#remember-status")).toContainText("Uloženo zde");
  expect(JSON.parse((await stored(page))!).inputs.riderKg).toBe(82.5);
  const report = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    report.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
  await page.locator(".setup-memory").screenshot({
    path: `test-results/${info.project.name}-remember-czech.png`,
  });
  for (const width of [820, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
    ).toBe(false);
  }
  await page.locator(".setup-memory").screenshot({
    path: `test-results/${info.project.name}-remember-narrow.png`,
  });
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(remember(page)).toBeChecked();
  await expect(page.locator("#remember-status")).toContainText("Saved here");
});

test("blocked storage leaves the app usable and never claims the setup was saved", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("Blocked", "SecurityError");
      },
    });
  });
  await page.goto("/?lang=en");
  await ready(page);
  await expect(page.locator("#remember-status")).toContainText(
    "storage is unavailable",
  );
  await remember(page).check();
  await page.getByLabel("Sustainable power", { exact: true }).fill("220");
  await ready(page);
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 17 min");
  await expect(page.locator("#remember-status")).toContainText(
    "can’t be saved",
  );
  await remember(page).uncheck();
  await expect(page.locator("#remember-status")).toContainText(
    "couldn’t be removed",
  );
  await expect(remember(page)).not.toBeChecked();
  await page.getByLabel("Sustainable power", { exact: true }).fill("230");
  await ready(page);
  await expect(page.locator("#remember-status")).toContainText("Saving is off");
  await page
    .getByRole("button", { name: "Remove saved setup", exact: true })
    .click();
  await expect(page.locator("#remember-status")).toContainText(
    "couldn’t be removed",
  );
});
