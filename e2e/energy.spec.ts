import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const ready = async (page: Page, cs = false) =>
  expect(page.getByRole("status")).toContainText(
    cs ? "Přehled aktualizován" : "Briefing updated",
  );

test("chart views share keyboard position and elapsed time without recalculating the ride", async ({
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
  const slider = page.getByLabel("Inspect route distance");
  const energy = page.getByRole("button", { name: "Energy", exact: true });
  const elevation = page.getByRole("button", {
    name: "Elevation",
    exact: true,
  });
  await expect(elevation).toHaveAttribute("aria-pressed", "true");
  const workers = await page.evaluate(() => (window as any).workerCount);
  const originalTime = await page.getByTestId("moving-time").innerText();
  await slider.focus();
  await slider.press("Home");
  await expect(page.getByTestId("profile-time")).toHaveText("0 min");
  await slider.press("ArrowRight");
  await expect(page.getByTestId("profile-time")).toHaveText("<1 min");
  await slider.press("End");
  await expect(page.getByTestId("profile-time")).toHaveText(originalTime);
  await energy.focus();
  await energy.press("Enter");
  await expect(energy).toHaveAttribute("aria-pressed", "true");
  await expect(slider).toHaveValue("1000");
  await expect(page.getByTestId("profile-time")).toHaveText(originalTime);
  await expect(page.getByTestId("profile-work")).toHaveText("880 kJ");
  await expect(page.getByTestId("profile-work-remaining")).toHaveText("0 kJ");
  await expect(slider).toHaveAttribute("aria-valuetext", /moving time.*880 kJ/);
  await slider.focus();
  await slider.press("Home");
  await expect(page.getByTestId("profile-work")).toHaveText("0 kJ");
  await expect(page.getByTestId("profile-work-remaining")).toHaveText("880 kJ");
  for (let n = 0; n < 5; n++) await slider.press("PageUp");
  const elapsed = await page.getByTestId("profile-time").innerText();
  const distance = await page.getByTestId("profile-distance").innerText();
  const work = await page.getByTestId("profile-work").innerText();
  await elevation.click();
  await expect(slider).toHaveValue("500");
  await expect(page.getByTestId("profile-time")).toHaveText(elapsed);
  await expect(page.getByTestId("profile-distance")).toHaveText(distance);
  await energy.click();
  await expect(page.getByTestId("profile-work")).toHaveText(work);
  await page.getByLabel("Language", { exact: true }).selectOption("cs");
  await expect(
    page.getByRole("button", { name: "Energie", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("profile-time")).toHaveText(elapsed);
  await expect(page.getByLabel("Prozkoumat místo na trase")).toHaveValue("500");
  await expect(page.getByLabel("Prozkoumat místo na trase")).toHaveAttribute(
    "aria-valuetext",
    /v pohybu, práce na pedálech/,
  );
  expect(await page.evaluate(() => (window as any).workerCount)).toBe(workers);
  await page.getByLabel("Udržitelný výkon", { exact: true }).fill("220");
  await ready(page, true);
  await expect(page.getByTestId("moving-time")).toHaveText("1 h 17 min");
  await expect(
    page.getByRole("button", { name: "Energie", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Prozkoumat místo na trase")).toHaveValue("500");
  await page.getByLabel("Prozkoumat místo na trase").press("End");
  await expect(page.getByTestId("profile-time")).toHaveText("1 h 17 min");
  await expect(page.getByTestId("profile-work-remaining")).toHaveText("0 kJ");
});

test("coasting has a zero-work chart with advancing time and separate tracks remain separate", async ({
  page,
}) => {
  await page.goto("/?lang=en");
  await ready(page);
  const lat = (m: number) => m / ((6371000 * Math.PI) / 180);
  const xml =
    '<gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>100</ele></trkpt><trkpt lat="' +
    lat(1000) +
    '" lon="0"><ele>50</ele></trkpt></trkseg><trkseg><trkpt lat="' +
    lat(10000) +
    '" lon="0"><ele>500</ele></trkpt><trkpt lat="' +
    lat(11000) +
    '" lon="0"><ele>450</ele></trkpt></trkseg></trk></gpx>';
  await page.locator("#gpx-file").setInputFiles({
    name: "two-descents.gpx",
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(xml),
  });
  await ready(page);
  await page.getByLabel("Sustainable power", { exact: true }).fill("0");
  await ready(page);
  await page.getByRole("button", { name: "Energy", exact: true }).click();
  const slider = page.getByLabel("Inspect route distance");
  await slider.focus();
  await slider.press("Home");
  await expect(page.getByTestId("profile-time")).toHaveText("0 min");
  await expect(page.getByTestId("profile-work")).toHaveText("0 kJ");
  await slider.press("End");
  await expect(page.getByTestId("profile-time")).toHaveText(
    await page.getByTestId("moving-time").innerText(),
  );
  await expect(page.getByTestId("profile-time")).not.toHaveText("0 min");
  await expect(page.getByTestId("profile-work")).toHaveText("0 kJ");
  await expect(page.getByTestId("profile-work-remaining")).toHaveText("0 kJ");
  await expect(page.locator(".profile svg polyline")).toHaveCount(2);
  const lines = await page
    .locator(".profile svg polyline")
    .evaluateAll((elements) =>
      elements.map((el) => el.getAttribute("points")!),
    );
  for (const line of lines) {
    expect(line).not.toMatch(/NaN|Infinity/);
    expect(
      line.split(" ").every((pair) => Number(pair.split(",")[1]) === 200),
    ).toBe(true);
  }
  await expect(page.locator(".energy-explanation")).toContainText(
    "your body still uses energy",
  );
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("energy and elevation stay accessible and readable in Czech and English on narrow screens", async ({
  page,
}, testInfo) => {
  await page.goto("/?lang=cs");
  await ready(page, true);
  await page.getByRole("button", { name: "Energie", exact: true }).click();
  await expect(
    page.getByRole("img", { name: /Práce na pedálech od startu/ }),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.locator(".profile-card").screenshot({
    path: "test-results/" + testInfo.project.name + "-energy-cs.png",
  });
  if (testInfo.project.name === "desktop") {
    const chart = page.locator(".profile svg");
    const bounds = await chart.boundingBox();
    await page.mouse.move(
      bounds!.x + bounds!.width * 0.7,
      bounds!.y + bounds!.height * 0.5,
    );
    const distance = await page.getByTestId("profile-distance").innerText();
    await page.getByRole("button", { name: "Výška", exact: true }).click();
    await expect(page.getByTestId("profile-distance")).toHaveText(distance);
  }
  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await page.getByRole("button", { name: "Energy", exact: true }).click();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.setViewportSize({ width: 320, height: 740 });
  for (const language of ["en", "cs"]) {
    await page.locator("#language").selectOption(language);
    for (const label of language === "cs"
      ? ["Energie", "Výška"]
      : ["Energy", "Elevation"]) {
      await page.getByRole("button", { name: label, exact: true }).click();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      const box = await page
        .getByRole("button", { name: label, exact: true })
        .boundingBox();
      expect(box!.height).toBeGreaterThanOrEqual(44);
    }
  }
  await page.getByRole("button", { name: "Energie", exact: true }).click();
  await page.locator(".profile-card").screenshot({
    path: "test-results/" + testInfo.project.name + "-energy-320.png",
  });
});
