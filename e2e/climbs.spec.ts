import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const ready = (page: Page, cs = false) =>
  expect(page.getByRole("status")).toContainText(
    cs ? "Přehled aktualizován" : "Briefing updated",
  );
const first = (page: Page) =>
  page.getByRole("button", { name: /^Show climb 1:/ });
test.use({ reducedMotion: "reduce" });

test("climb selection links both charts, preserves whole-route inspection and works with a keyboard", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const NativeWorker = window.Worker;
    (window as any).workerCount = 0;
    window.Worker = class extends NativeWorker {
      constructor(url: string | URL, options?: WorkerOptions) {
        super(url, options);
        (window as any).workerCount++;
      }
    };
  });
  await page.goto("/?lang=en");
  await ready(page);
  const workers = await page.evaluate(() => (window as any).workerCount);
  await first(page).focus();
  await first(page).press("Enter");
  await expect(
    page.getByRole("region", { name: "Ride chart", exact: true }),
  ).toBeFocused();
  await expect(first(page)).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("climb-selection")).toContainText(
    "Climb 1 · 8.0–12.0 km",
  );
  await expect(page.getByTestId("climb-time")).toHaveText("19 min");
  await expect(page.getByTestId("climb-cadence")).toHaveText("88 rpm");
  await expect(page.getByTestId("profile-distance")).toHaveText("8.0 km");
  const work = await page.getByTestId("climb-work").innerText();
  expect(parseInt(work)).toBeGreaterThan(100);
  const highlight = page.getByTestId("climb-highlight");
  expect(
    Number(await highlight.locator("rect").getAttribute("width")),
  ).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Energy", exact: true }).click();
  await expect(highlight).toBeVisible();
  await expect(page.getByTestId("climb-work")).toHaveText(work);
  const slider = page.getByLabel("Inspect route distance");
  await slider.focus();
  await slider.press("End");
  await expect(page.getByTestId("profile-distance")).toHaveText("38.0 km");
  await expect(page.getByTestId("climb-work")).toHaveText(work);
  await page.getByRole("button", { name: /^Show climb 2:/ }).click();
  await expect(first(page)).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByTestId("climb-selection")).toContainText(
    "Climb 2 · 27.0–30.0 km",
  );
  await expect(page.getByTestId("profile-distance")).toHaveText("27.0 km");
  await page.getByRole("button", { name: "Elevation", exact: true }).click();
  await expect(highlight).toBeVisible();
  await page
    .getByRole("button", { name: "Clear selection", exact: true })
    .click();
  await expect(page.getByTestId("climb-selection")).toHaveCount(0);
  await expect(highlight).toHaveCount(0);
  await expect(
    page.getByRole("region", { name: "Ride chart", exact: true }),
  ).toBeFocused();
  await expect(page.getByTestId("profile-distance")).toHaveText("27.0 km");
  expect(await page.evaluate(() => (window as any).workerCount)).toBe(workers);
});

test("selected totals update with power and gearing without confusing cadence with ride time", async ({
  page,
}) => {
  await page.goto("/?lang=en");
  await ready(page);
  await first(page).click();
  const originalWork = await page.getByTestId("climb-work").innerText();
  await page.getByLabel("Sustainable power", { exact: true }).fill("220");
  await ready(page);
  await expect(first(page)).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("climb-time")).not.toHaveText("19 min");
  await expect(page.getByTestId("climb-work")).not.toHaveText(originalWork);
  const time = await page.getByTestId("climb-time").innerText();
  const work = await page.getByTestId("climb-work").innerText();
  const cadence = await page.getByTestId("climb-cadence").innerText();
  await page
    .locator("summary")
    .filter({ hasText: "Gearing & cadence" })
    .click();
  await page.getByLabel("Front chainrings", { exact: true }).fill("50");
  await page.getByLabel("Front chainrings", { exact: true }).press("Tab");
  await page.getByLabel("Cassette cogs", { exact: true }).fill("11");
  await page.getByLabel("Cassette cogs", { exact: true }).press("Tab");
  await ready(page);
  await expect(page.getByTestId("climb-time")).toHaveText(time);
  await expect(page.getByTestId("climb-work")).toHaveText(work);
  await expect(page.getByTestId("climb-cadence")).not.toHaveText(cadence);
  await page.getByLabel("Sustainable power", { exact: true }).fill("");
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByTestId("climb-selection")).toHaveCount(0);
  await page.getByLabel("Sustainable power", { exact: true }).fill("180");
  await ready(page);
  await expect(page.getByTestId("climb-highlight")).toHaveCount(0);
});

test("new GPX, smoothing and demo reset clear a selection even when filenames match", async ({
  page,
}) => {
  await page.goto("/?lang=en");
  await ready(page);
  const lat = (m: number) => m / ((6371000 * Math.PI) / 180);
  const gpx = (flat = false) =>
    `<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>0</ele></trkpt><trkpt lat="${lat(500)}" lon="0"><ele>${flat ? 0 : 25}</ele></trkpt></trkseg><trkseg><trkpt lat="${lat(10000)}" lon="0"><ele>300</ele></trkpt><trkpt lat="${lat(10400)}" lon="0"><ele>${flat ? 300 : 320}</ele></trkpt></trkseg></trk></gpx>`;
  const upload = (xml: string) =>
    page.locator("#gpx-file").setInputFiles({
      name: "same-name.gpx",
      mimeType: "application/gpx+xml",
      buffer: Buffer.from(xml),
    });
  await first(page).click();
  await upload(gpx());
  await ready(page);
  await expect(page.getByTestId("climb-selection")).toHaveCount(0);
  await expect(page.locator(".climb-row")).toHaveCount(2);
  await page.getByRole("button", { name: /^Show climb 2:/ }).click();
  await expect(page.getByTestId("climb-highlight")).toBeVisible();
  await page
    .getByLabel("Elevation smoothing", { exact: false })
    .selectOption("0");
  await ready(page);
  await expect(page.getByTestId("climb-selection")).toHaveCount(0);
  await first(page).click();
  await upload(gpx(true));
  await ready(page);
  await expect(page.locator(".climb-row")).toHaveCount(0);
  await expect(page.getByTestId("climb-highlight")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Return to demo & clear GPX", exact: true })
    .click();
  await ready(page);
  await expect(page.getByTestId("climb-selection")).toHaveCount(0);
  await first(page).click();
  await expect(page.getByTestId("climb-selection")).toContainText(
    "8.0–12.0 km",
  );
});

test("Czech selection is accessible and readable in both views at phone widths", async ({
  page,
}, info) => {
  await page.goto("/?lang=cs");
  await ready(page, true);
  await page.getByRole("button", { name: /^Zobrazit stoupání 1:/ }).click();
  await expect(page.getByTestId("climb-selection")).toContainText(
    "Stoupání 1 · 8,0–12,0 km",
  );
  await expect(page.getByTestId("climb-cadence")).toHaveText("88 ot/min");
  await page.locator(".profile-card").screenshot({
    path: `test-results/${info.project.name}-climb-elevation.png`,
  });
  await page.getByRole("button", { name: "Energie", exact: true }).click();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page
    .locator(".profile-card")
    .screenshot({ path: `test-results/${info.project.name}-climb-energy.png` });
  await page
    .locator(".demanding")
    .screenshot({ path: `test-results/${info.project.name}-climb-cards.png` });
  await page.setViewportSize({ width: 320, height: 740 });
  for (const view of ["Výška", "Energie"]) {
    await page.getByRole("button", { name: view, exact: true }).click();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await expect(page.getByTestId("climb-highlight")).toBeVisible();
  }
  await page
    .locator(".profile-card")
    .screenshot({ path: `test-results/${info.project.name}-climb-320.png` });
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(page.getByTestId("climb-selection")).toContainText(
    "Climb 1 · 8.0–12.0 km",
  );
  await expect(first(page)).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("button", { name: "Energy", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});
