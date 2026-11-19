import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";
const ready = (page: Page, cs = false) =>
  expect(page.getByRole("status")).toContainText(
    cs ? "Přehled aktualizován" : "Briefing updated",
  );
const start = async (page: Page) => {
  await page.goto("/?lang=en");
  await ready(page);
  await page
    .getByRole("button", { name: "Build my plan", exact: true })
    .click();
};
test.use({ reducedMotion: "reduce" });

test("plan separates expenditure and intake, preserves simulation and supports chart timing in both views", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const Native = window.Worker;
    (window as any).workers = 0;
    window.Worker = class extends Native {
      constructor(url: string | URL, options?: WorkerOptions) {
        super(url, options);
        (window as any).workers++;
      }
    };
  });
  const outbound: string[] = [];
  page.on("request", (r) => {
    if (
      !r
        .url()
        .startsWith(
          new URL(process.env.BETA_URL ?? "http://127.0.0.1:4173").origin,
        ) &&
      !r.url().startsWith("blob:")
    )
      outbound.push(r.url());
  });
  await start(page);
  const count = await page.evaluate(() => (window as any).workers);
  await expect(page.getByTestId("fuel-carbs")).toHaveText("64 g");
  await expect(page.getByTestId("fuel-intake")).toContainText("260 kcal");
  await expect(page.getByTestId("fuel-expenditure")).toContainText(
    "850–1,150 kcal",
  );
  await expect(page.getByTestId("plan-markers")).toBeVisible();
  await page
    .getByLabel("Carbohydrate target", { exact: true })
    .selectOption("60");
  await expect(page.getByTestId("fuel-carbs")).toHaveText("86 g");
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 26 min");
  await page.getByRole("button", { name: "Energy", exact: true }).click();
  await page.getByLabel("Inspect route distance").press("End");
  await expect(page.getByTestId("profile-carbs")).toContainText("86 g");
  await expect(page.getByTestId("profile-work")).toHaveText("880 kJ");
  await page
    .locator("summary")
    .filter({ hasText: "Fuel timing along the route" })
    .click();
  await page
    .getByRole("button", { name: "Inspect fuel window 1", exact: true })
    .click();
  await expect(page.getByTestId("profile-time")).toHaveText("10 min");
  await expect(page.getByTestId("profile-carbs")).toContainText("10 g");
  await page.getByRole("button", { name: /^Show climb 1:/ }).click();
  await expect(page.getByTestId("climb-selection")).toContainText("kJ/km");
  await page.getByRole("button", { name: "Elevation", exact: true }).click();
  await expect(page.getByTestId("plan-markers")).toBeVisible();
  await expect(page.getByTestId("climb-highlight")).toBeVisible();
  expect(await page.evaluate(() => (window as any).workers)).toBe(count);
  expect(outbound).toEqual([]);
});

test("bottle shortages, manual/chart stops, exact refill readout and downloads agree", async ({
  page,
}) => {
  await start(page);
  await page.getByLabel("Planning drinking rate", { exact: true }).fill("1500");
  await expect(page.getByTestId("fuel-coverage")).toContainText(
    "Bottles run out",
  );
  await page.getByLabel("Refill at distance", { exact: true }).fill("15");
  await page
    .getByRole("button", { name: "Add refill stop", exact: true })
    .click();
  await expect(page.getByTestId("fuel-coverage")).not.toContainText(
    "Bottles run out",
  );
  await page.getByRole("button", { name: /^Refill 1 ·/ }).click();
  await expect(page.getByTestId("profile-distance")).toHaveText("15.0 km");
  await expect(page.getByTestId("profile-water")).toHaveText("1.5 l");
  await page
    .getByRole("button", { name: "Add water refill here", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("at least 10 m");
  await page.getByLabel("Inspect route distance").fill("700");
  await page
    .getByRole("button", { name: "Add water refill here", exact: true })
    .click();
  await expect(page.locator(".fuel-stop-list li")).toHaveCount(2);
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download ride briefing", exact: true })
    .click();
  const text = await readFile((await (await download).path())!, "utf8");
  expect(text).toContain("Planned carbohydrate intake: 64 g");
  expect(text).toContain("Refill 1: 15.0 km");
  expect(text).toContain("Refill 2: 26.6 km");
  expect(text).toContain("0 min–20 min");
  expect(text).toContain("not predicted thirst");
  await page
    .getByRole("button", { name: "Remove refill 2", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Remove refill 1", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Add refill stop", exact: true }),
  ).toBeFocused();
  await expect(page.getByTestId("fuel-coverage")).toContainText(
    "Bottles run out",
  );
});

test("invalid plan edits suppress totals and markers without losing the route or exporting stale values", async ({
  page,
}) => {
  await start(page);
  for (const [label, value] of [
    ["Planning drinking rate", ""],
    ["Number of bottles", "1.5"],
    ["Volume per bottle", "-1"],
  ]) {
    await page.getByLabel(label, { exact: true }).fill(value);
    await expect(page.getByTestId("fuel-carbs")).toHaveCount(0);
    await expect(page.getByTestId("plan-markers")).toHaveCount(0);
    await expect(page.getByRole("alert")).toContainText("Check plan inputs");
    const download = page.waitForEvent("download");
    await page
      .getByRole("button", { name: "Download ride briefing", exact: true })
      .click();
    expect(await readFile((await (await download).path())!, "utf8")).toContain(
      "no intake or bottle coverage is exported",
    );
    await page
      .getByLabel(label, { exact: true })
      .fill(
        label === "Planning drinking rate"
          ? "500"
          : label === "Number of bottles"
            ? "2"
            : "750",
      );
    await expect(page.getByTestId("fuel-carbs")).toBeVisible();
  }
  await page.getByLabel("Refill at distance", { exact: true }).fill("999");
  await page
    .getByRole("button", { name: "Add refill stop", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("inside the route");
  await expect(page.locator(".fuel-stop-list li")).toHaveCount(0);
  await page
    .getByLabel("Carbohydrate target", { exact: true })
    .selectOption("90");
  await expect(page.locator(".fuel-planner")).toContainText("Above 60 g/h");
  await page
    .getByLabel("Carbohydrate target", { exact: true })
    .selectOption("0");
  await expect(page.getByTestId("fuel-carbs")).toHaveText("0 g");
  await expect(page.locator(".fuel-planner")).toContainText(
    "No carbohydrate intake is planned",
  );
});

test("power updates preserve stop location, new routes clear stops, and plans are never persisted", async ({
  page,
}) => {
  await start(page);
  await page
    .getByLabel("Remember my setup on this device", { exact: true })
    .check();
  await page.getByLabel("Refill at distance", { exact: true }).fill("12");
  await page
    .getByRole("button", { name: "Add refill stop", exact: true })
    .click();
  const before = await page.getByTestId("fuel-carbs").innerText();
  await page.getByLabel("Sustainable power", { exact: true }).fill("220");
  await ready(page);
  await expect(page.getByTestId("fuel-carbs")).not.toHaveText(before);
  await expect(page.locator(".fuel-stop-list")).toContainText("12.0 km");
  await page
    .getByLabel("Carbohydrate target", { exact: true })
    .selectOption("75");
  await page.reload();
  await ready(page);
  await expect(
    page.getByRole("button", { name: "Build my plan", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Build my plan", exact: true })
    .click();
  await expect(
    page.getByLabel("Carbohydrate target", { exact: true }),
  ).toHaveValue("auto");
  await expect(page.locator(".fuel-stop-list li")).toHaveCount(0);
  await page
    .getByLabel("Remember my setup on this device", { exact: true })
    .uncheck();
  const upload = () =>
    page.locator("#gpx-file").setInputFiles({
      name: "same.gpx",
      mimeType: "application/gpx+xml",
      buffer: Buffer.from(
        '<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>0</ele></trkpt><trkpt lat="0.01" lon="0"><ele>20</ele></trkpt></trkseg><trkseg><trkpt lat="1" lon="0"><ele>50</ele></trkpt><trkpt lat="1.01" lon="0"><ele>60</ele></trkpt></trkseg></trk></gpx>',
      ),
    });
  await upload();
  await ready(page);
  await expect(page.locator(".fuel-planner")).toContainText(
    "Track breaks omit travel",
  );
  await expect(page.getByTestId("fuel-carbs")).toHaveText("0 g");
  await page.getByLabel("Refill at distance", { exact: true }).fill("1");
  await page
    .getByRole("button", { name: "Add refill stop", exact: true })
    .click();
  await upload();
  await ready(page);
  await expect(page.locator(".fuel-stop-list li")).toHaveCount(0);
  await page.getByLabel("Refill at distance", { exact: true }).fill("1");
  await page
    .getByRole("button", { name: "Add refill stop", exact: true })
    .click();
  await page
    .getByLabel("Elevation smoothing", { exact: false })
    .selectOption("0");
  await ready(page);
  await expect(page.locator(".fuel-stop-list li")).toHaveCount(0);
});

test("Czech plan, decimal inputs, translated download and narrow layouts stay accessible", async ({
  page,
}, info) => {
  await page.goto("/?lang=cs");
  await ready(page, true);
  await page
    .getByRole("button", { name: "Sestavit plán", exact: true })
    .click();
  await page
    .getByLabel("Doplnění na vzdálenosti", { exact: true })
    .fill("12,5");
  await page
    .getByRole("button", { name: "Přidat doplnění vody", exact: true })
    .click();
  await expect(page.locator(".fuel-stop-list")).toContainText("12,5 km");
  await page
    .locator("summary")
    .filter({ hasText: "Rozvrh příjmu sacharidů na trase" })
    .click();
  await page
    .locator(".fuel-planner")
    .screenshot({ path: `test-results/${info.project.name}-fuel-plan.png` });
  await page.getByRole("button", { name: /^Zobrazit stoupání 1:/ }).click();
  await page.getByRole("button", { name: "Energie", exact: true }).click();
  await page
    .locator(".profile-card")
    .screenshot({ path: `test-results/${info.project.name}-fuel-chart.png` });
  await page
    .locator("summary")
    .filter({ hasText: "Rezerva, doporučení a předpoklady" })
    .click();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.setViewportSize({ width: 320, height: 740 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page
    .locator(".fuel-planner")
    .screenshot({ path: `test-results/${info.project.name}-fuel-320.png` });
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Stáhnout přehled jízdy", exact: true })
    .click();
  const txt = await readFile((await (await download).path())!, "utf8");
  expect(txt).toContain("Plán jídla a pití");
  expect(txt).toContain("Doplnění 1: 12,5 km");
  expect(txt).not.toContain("{grams}");
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(page.locator(".fuel-stop-list")).toContainText("12.5 km");
  await page.getByRole("button", { name: "Hide plan", exact: true }).click();
  await expect(page.getByTestId("plan-markers")).toHaveCount(0);
});

test("coasting keeps body-energy caveats and fluid planning despite zero crank work", async ({
  page,
}) => {
  await start(page);
  await page.locator("#gpx-file").setInputFiles({
    name: "coast.gpx",
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(
      '<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>300</ele></trkpt><trkpt lat="0.01" lon="0"><ele>240</ele></trkpt></trkseg></trk></gpx>',
    ),
  });
  await ready(page);
  await page.getByLabel("Sustainable power", { exact: true }).fill("0");
  await ready(page);
  await expect(page.getByTestId("fuel-expenditure")).toHaveText("0–0 kcal");
  await expect(page.getByTestId("fuel-carbs")).toHaveText("0 g");
  await expect(page.locator(".fuel-planner")).toContainText(
    "Zero modeled work does not mean zero body energy use",
  );
  await page
    .getByLabel("Carbohydrate target", { exact: true })
    .selectOption("30");
  await expect(page.getByTestId("fuel-carbs")).not.toHaveText("0 g");
  await page.getByRole("button", { name: "Energy", exact: true }).click();
  await page.getByLabel("Inspect route distance").press("End");
  await expect(page.getByTestId("profile-work")).toHaveText("0 kJ");
  await expect(page.getByTestId("profile-carbs")).not.toHaveText(
    "0 g · ≈ 0 kcal",
  );
});
