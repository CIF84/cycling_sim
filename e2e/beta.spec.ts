import { test, expect } from "@playwright/test";
import path from "node:path";
import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";
const fixture = (name: string) => path.resolve("e2e/fixtures", name);
const ready = async (page: any) =>
  expect(page.getByRole("status")).toContainText("Briefing updated");
test("demo, inputs, gearing, wind, comparisons, keyboard chart and local download", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
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
  await page.goto("/");
  await ready(page);
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 26 min");
  await expect(
    page.getByRole("heading", { name: "Small changes. This route." }),
  ).toBeVisible();
  const bars = await page
    .locator(".saving-bar > span")
    .evaluateAll((elements) =>
      elements.map(
        (el) =>
          el.getBoundingClientRect().width /
          el.parentElement!.getBoundingClientRect().width,
      ),
    );
  expect(bars).toHaveLength(4);
  expect(bars.every((width) => width > 0 && width <= 1.001)).toBe(true);
  expect(bars[0]).toBeGreaterThan(bars[1]);
  expect(bars[1]).toBeGreaterThan(bars[2]);
  await page.getByLabel("Sustainable power", { exact: true }).fill("220");
  await ready(page);
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 17 min");
  await page
    .getByLabel("Surface & tires", { exact: false })
    .selectOption("0.008");
  await ready(page);
  const gravel = await page.getByTestId("moving-time").innerText();
  expect(gravel).not.toBe("1 h 17 min");
  await page
    .locator("summary")
    .filter({ hasText: "Gearing & cadence" })
    .click();
  await page.getByLabel("Front chainrings", { exact: false }).fill("50");
  await page.getByLabel("Front chainrings", { exact: false }).press("Tab");
  await ready(page);
  await expect(page.getByTestId("moving-time")).toHaveText(gravel);
  await page
    .locator("summary")
    .filter({ hasText: "Conditions & model" })
    .click();
  await page.getByLabel("Along-route wind", { exact: true }).fill("20");
  await ready(page);
  expect(await page.getByTestId("moving-time").innerText()).not.toBe(gravel);
  await page.getByRole("button", { name: "Reset ride inputs" }).click();
  await ready(page);
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 26 min");
  await page.getByLabel("Inspect route distance").focus();
  await page.getByLabel("Inspect route distance").press("ArrowRight");
  expect(await page.getByLabel("Inspect route distance").inputValue()).toBe(
    "321",
  );
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download ride briefing" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("bike-science-briefing.txt");
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
  expect(errors).toEqual([]);
  expect(outbound).toEqual([]);
  await page.goto("/");
  await ready(page);
  await page.screenshot({
    path: `test-results/${testInfo.project.name}-demo.png`,
    fullPage: true,
  });
  await page.screenshot({
    path: `test-results/${testInfo.project.name}-overview.png`,
    fullPage: false,
  });
});
test("GPX stays local; quality, elevation and malformed files have recoverable states", async ({
  page,
}) => {
  const writes: string[] = [];
  page.on("request", (r) => {
    if (r.method() !== "GET") writes.push(r.url());
  });
  await page.goto("/");
  await ready(page);
  await page.locator("#gpx-file").setInputFiles(fixture("synthetic.gpx"));
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "synthetic", exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("moving-time")).toHaveText("5 min");
  await page.getByText("Route quality", { exact: true }).click();
  await expect(page.getByText(/Recorded ascent: 50 m/)).toBeVisible();
  await page
    .getByLabel("Elevation smoothing", { exact: false })
    .selectOption("0");
  await ready(page);
  await page
    .locator("#gpx-file")
    .setInputFiles(fixture("missing-elevation.gpx"));
  await expect(page.getByRole("alert")).toContainText("no elevation data");
  await expect(page.getByTestId("moving-time")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Reset setup & try the demo" })
    .click();
  await ready(page);
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 26 min");
  await page.locator("#gpx-file").setInputFiles(fixture("broken.gpx"));
  await expect(page.getByRole("alert")).toContainText("not valid GPX XML");
  await page
    .getByRole("button", { name: "Reset setup & try the demo" })
    .click();
  await ready(page);
  await page.getByLabel("Sustainable power", { exact: true }).fill("0");
  await expect(page.getByRole("alert")).toContainText("cannot keep you moving");
  await page.getByLabel("Sustainable power", { exact: true }).fill("180");
  await ready(page);
  await page.getByLabel("Rider weight", { exact: true }).fill("999");
  await expect(page.getByRole("alert")).toContainText("Rider weight must be");
  await page.getByRole("button", { name: "Reset ride inputs" }).click();
  await ready(page);
  expect(writes).toEqual([]);
});

test("accessible default and advanced form", async ({ page }) => {
  await page.goto("/");
  await ready(page);
  await page
    .locator("summary")
    .filter({ hasText: "Conditions & model" })
    .click();
  await page
    .locator("summary")
    .filter({ hasText: "Gearing & cadence" })
    .click();
  const report = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    report.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => ({
        target: n.target,
        summary: n.failureSummary,
      })),
    })),
  ).toEqual([]);
});

test("larger import keeps inputs responsive and superseded jobs do not win", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page);
  const points = Array.from(
    { length: 20000 },
    (_, n) =>
      `<trkpt lat="${(n * 0.00001).toFixed(5)}" lon="0"><ele>100</ele></trkpt>`,
  ).join("");
  await page.locator("#gpx-file").setInputFiles({
    name: "large-synthetic.gpx",
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(`<gpx><trk><trkseg>${points}</trkseg></trk></gpx>`),
  });
  await page.getByLabel("Sustainable power", { exact: true }).fill("210");
  await page.getByLabel("Sustainable power", { exact: true }).fill("230");
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "large-synthetic", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("230 → 253 W", { exact: true })).toBeVisible();
  await expect(page.getByText(/20,000 source points/)).toBeVisible();
});

test("profile grade stays on the section under the cursor", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page);
  const lat = (meters: number) => meters / ((6371000 * Math.PI) / 180);
  await page.locator("#gpx-file").setInputFiles({
    name: "flat-then-climb.gpx",
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(
      `<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>100</ele></trkpt><trkpt lat="${lat(100)}" lon="0"><ele>100</ele></trkpt><trkpt lat="${lat(220)}" lon="0"><ele>112</ele></trkpt></trkseg></trk></gpx>`,
    ),
  });
  await page
    .getByLabel("Elevation smoothing", { exact: false })
    .selectOption("0");
  await ready(page);
  const slider = page.getByLabel("Inspect route distance");
  await slider.focus();
  await slider.press("Home");
  for (let i = 0; i < 4; i++) await slider.press("PageUp");
  await expect(slider).toHaveValue("400");
  await expect(page.locator(".chart-readout")).toHaveText(/\s0\.0% grade/);
});

test("valid coasting briefing survives an unavailable comparison and exports its explanation", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await ready(page);
  await page.locator("#gpx-file").setInputFiles({
    name: "flat-coasting.gpx",
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(
      '<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>100</ele></trkpt><trkpt lat="0.009" lon="0"><ele>100</ele></trkpt></trkseg></trk></gpx>',
    ),
  });
  await ready(page);
  await page
    .locator("summary")
    .filter({ hasText: "Conditions & model" })
    .click();
  await page.getByLabel("Along-route wind", { exact: true }).fill("-17");
  await ready(page);
  await page.getByLabel("Sustainable power", { exact: true }).fill("0");
  await ready(page);
  await expect(page.getByTestId("moving-time")).toBeVisible();
  const unavailable = page
    .locator(".comparison-row")
    .filter({ hasText: "10% lower aerodynamic drag" });
  await expect(unavailable).toContainText("Unavailable.");
  await expect(unavailable).toContainText("baseline briefing is still valid");
  await expect(unavailable.locator(".saving-bar")).toHaveCount(0);
  await expect(page.getByRole("alert")).toHaveCount(0);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download ride briefing" }).click();
  const download = await downloadPromise;
  const content = await readFile((await download.path())!, "utf8");
  expect(content).toContain("Sustainable crank power: 0 W");
  expect(content).toContain("10% lower aerodynamic drag: unavailable.");
  expect(content).not.toMatch(/NaN|Infinity/);
  await page.locator("#comparisons").screenshot({
    path: `test-results/${testInfo.project.name}-unavailable.png`,
  });
});

test("smoothed descent keeps its final remainder and zero time savings are not ranked as gains", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page);
  const endLat = 1001 / ((6371000 * Math.PI) / 180);
  await page.locator("#gpx-file").setInputFiles({
    name: "steady-descent.gpx",
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(
      `<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>100</ele></trkpt><trkpt lat="${endLat}" lon="0"><ele>49.95</ele></trkpt></trkseg></trk></gpx>`,
    ),
  });
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "steady-descent", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page
    .locator("summary")
    .filter({ hasText: "Conditions & model" })
    .click();
  await page.getByLabel("Speed ceiling", { exact: true }).fill("15");
  await ready(page);
  await expect(page.getByTestId("moving-time")).toHaveText("4 min");
  await expect(page.locator(".comparison-insight")).toContainText(
    "None of these changes saves modeled time",
  );
  await expect(page.locator(".comparison-icon.best")).toHaveCount(0);
});
