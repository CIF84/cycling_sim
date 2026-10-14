import { test, expect } from "@playwright/test";
import path from "node:path";
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
