import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
const ready = (page: Page, cs = true) =>
  expect(page.getByRole("status")).toContainText(
    cs ? "Přehled aktualizován" : "Briefing updated",
  );
test.use({ locale: "cs-CZ" });

test("Czech browser default, accessible layout and retained explicit language preference", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await ready(page);
  await expect(page.locator("html")).toHaveAttribute("lang", "cs");
  await expect(page).toHaveTitle("Bike Science Pro · Na kolo s plánem");
  await expect(
    page.getByRole("heading", { name: "Nedělní okruh", exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 26 min");
  await expect(
    page.locator(".metric").filter({ hasText: "Délka trasy" }),
  ).toContainText("38,0");
  await page.screenshot({
    path: `test-results/${info.project.name}-czech-overview.png`,
  });
  await page.locator("summary").filter({ hasText: "Podmínky a model" }).click();
  await page
    .locator("summary")
    .filter({ hasText: "Převody a kadence" })
    .click();
  await expect(
    page.getByLabel("Aerodynamický odpor (CdA)", { exact: true }),
  ).toHaveValue("0,35");
  await page
    .locator("summary")
    .filter({ hasText: "Předpoklady a omezení" })
    .click();
  await page
    .locator("summary")
    .filter({ hasText: "Soukromí a rozsah bety" })
    .click();
  const report = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    report.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page.screenshot({
    path: `test-results/${info.project.name}-czech-full.png`,
    fullPage: true,
  });
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.goto("/");
  await ready(page, false);
  await expect(page.getByLabel("Language", { exact: true })).toHaveValue("en");
  await page.goto("/?lang=cs");
  await ready(page);
  expect(errors).toEqual([]);
});

test("language changes preserve inputs and calculations; decimal commas and validation work", async ({
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
  await ready(page, false);
  await page.getByLabel("Sustainable power", { exact: true }).fill("220");
  await ready(page, false);
  const workers = await page.evaluate(() => (window as any).workerCount);
  const baseline = await page.getByTestId("moving-time").innerText();
  await page.getByLabel("Language", { exact: true }).selectOption("cs");
  await ready(page);
  await expect(
    page.getByLabel("Udržitelný výkon", { exact: true }),
  ).toHaveValue("220");
  await expect(page.getByTestId("moving-time")).toHaveText(baseline);
  expect(await page.evaluate(() => (window as any).workerCount)).toBe(workers);
  await page.getByLabel("Hmotnost jezdce", { exact: true }).fill("75,5");
  await ready(page);
  await page.locator("summary").filter({ hasText: "Podmínky a model" }).click();
  await page.getByLabel("Valivý odpor (Crr)", { exact: true }).fill("0,006");
  await ready(page);
  await expect(
    page.getByText("Crr 0,0060 → 0,0048", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Valivý odpor (Crr)", { exact: true }).fill("0,00x");
  await expect(page.getByRole("alert")).toContainText(
    "Valivý odpor: zadejte hodnotu od 0,001 do 0,03.",
  );
  await expect(
    page.getByLabel("Valivý odpor (Crr)", { exact: true }),
  ).toHaveValue("0,00x");
  const errorWorkers = await page.evaluate(() => (window as any).workerCount);
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(page.getByRole("alert")).toContainText(
    "Rolling resistance must be between 0.001 and 0.03.",
  );
  expect(await page.evaluate(() => (window as any).workerCount)).toBe(
    errorWorkers,
  );
  await expect(page.getByLabel("Rider weight", { exact: true })).toHaveValue(
    "75.5",
  );
  await page
    .getByLabel("Rolling resistance (Crr)", { exact: true })
    .fill("0.006");
  await ready(page, false);
});

test("Czech GPX warnings, filenames, profile, download and errors stay local and switch live", async ({
  page,
}) => {
  const writes: string[] = [];
  page.on("request", (r) => {
    if (r.method() !== "GET") writes.push(r.url());
  });
  await page.goto("/?lang=cs");
  await ready(page);
  await page.locator("#gpx-file").setInputFiles({
    name: "The Sunday Loop.gpx",
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(
      '<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>100</ele></trkpt><trkpt lat="0" lon="0"><ele>100</ele></trkpt><trkpt lat="0.001" lon="0"/><trkpt lat="0.002" lon="0"><ele>110</ele></trkpt></trkseg></trk></gpx>',
    ),
  });
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "The Sunday Loop", exact: true }),
  ).toBeVisible();
  await page.getByText("Kvalita dat trasy", { exact: true }).click();
  await expect(page.locator(".quality")).toContainText(
    "Odstraněné duplicitní nebo téměř totožné body: 1.",
  );
  await expect(page.locator(".quality")).toContainText(
    "Doplněné chybějící výšky: 1.",
  );
  const slider = page.getByLabel("Prozkoumat místo na trase");
  await slider.focus();
  await slider.press("ArrowRight");
  await expect(slider).toHaveAttribute("aria-valuetext", /km, nadmořská výška/);
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(page.locator(".quality")).toContainText(
    "1 duplicate or near-identical points removed.",
  );
  await expect(
    page.getByRole("heading", { name: "The Sunday Loop", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Language", { exact: true }).selectOption("cs");
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Stáhnout přehled jízdy" }).click();
  const download = await downloaded;
  expect(download.suggestedFilename()).toBe("bike-science-prehled.txt");
  const content = await readFile((await download.path())!, "utf8");
  expect(content).toContain("The Sunday Loop");
  expect(content).toContain("Odhad času v pohybu:");
  expect(content).toContain("CdA 0,35 m² · Crr 0,005");
  expect(content).toContain(
    "Odstraněné duplicitní nebo téměř totožné body: 1.",
  );
  expect(content).toContain("O 10 % vyšší udržitelný výkon");
  expect(content).not.toMatch(/NaN|Infinity|\{\w+\}|<trkpt|lat=/);
  await page
    .locator("#gpx-file")
    .setInputFiles(path.resolve("e2e/fixtures/missing-elevation.gpx"));
  await expect(page.getByRole("alert")).toContainText(
    "Jeden úsek nemá výškové údaje.",
  );
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(page.getByRole("alert")).toContainText(
    "A track has no elevation data.",
  );
  await page.getByLabel("Language", { exact: true }).selectOption("cs");
  await page
    .getByRole("button", { name: "Obnovit nastavení a vyzkoušet ukázku" })
    .click();
  await ready(page);
  await page.locator("#gpx-file").setInputFiles({
    name: "wrong.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("not a GPX"),
  });
  await expect(page.getByRole("alert")).toContainText(
    "Vyberte soubor s příponou .gpx.",
  );
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 26 min");
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([
    "bike-science-language",
  ]);
  expect(writes).toEqual([]);
});

test("language selection works when browser storage is unavailable", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => {
      throw new Error("Storage disabled");
    };
    Storage.prototype.setItem = () => {
      throw new Error("Storage disabled");
    };
  });
  await page.goto("/?lang=cs");
  await ready(page);
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await ready(page, false);
  await expect(page).toHaveURL(/lang=en/);
  await page.reload();
  await ready(page, false);
});
