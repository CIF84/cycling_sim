import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";

const ready = (page: Page, cs = false) =>
  expect(page.getByRole("status")).toContainText(
    cs ? "Přehled aktualizován" : "Briefing updated",
  );

test("groupset presets apply both gear lists, retain other inputs, and support custom edits and reset", async ({
  page,
}) => {
  await page.goto("/?lang=en");
  await ready(page);
  await page.getByLabel("Sustainable power", { exact: true }).fill("100");
  await ready(page);
  const time = await page.getByTestId("moving-time").innerText();
  const comparisons = await page
    .locator(".saving-bar > span")
    .evaluateAll((els) => els.map((e) => e.getAttribute("style")));
  await page
    .locator("summary")
    .filter({ hasText: "Gearing & cadence" })
    .click();
  const selector = page.getByLabel("Groupset preset", { exact: true });
  const rings = page.getByLabel("Front chainrings", { exact: true });
  const cogs = page.getByLabel("Cassette cogs", { exact: true });
  await expect(selector).toHaveValue("shimano-105-r7100");
  await selector.selectOption("shimano-dura-ace-r9200");
  await ready(page);
  await expect(rings).toHaveValue("36, 52");
  await expect(cogs).toHaveValue(
    "11, 12, 13, 14, 15, 16, 17, 19, 21, 24, 27, 30",
  );
  await expect(
    page.getByText("Lowest ratio 36/30", { exact: false }),
  ).toBeVisible();
  await selector.selectOption("shimano-grx-rx820-1x51");
  await ready(page);
  await expect(rings).toHaveValue("40");
  await expect(cogs).toHaveValue(
    "10, 12, 14, 16, 18, 21, 24, 28, 33, 39, 45, 51",
  );
  await expect(
    page.getByText("Lowest ratio 40/51", { exact: false }),
  ).toBeVisible();
  await selector.selectOption("sram-rival-xplr-e1");
  await ready(page);
  await expect(cogs).toHaveValue(
    "10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 46",
  );
  await expect(page.getByTestId("gearing-preset")).toContainText("1×13");
  await expect(page.getByTestId("moving-time")).toHaveText(time);
  await expect(
    page.getByLabel("Sustainable power", { exact: true }),
  ).toHaveValue("100");
  expect(
    await page
      .locator(".saving-bar > span")
      .evaluateAll((els) => els.map((e) => e.getAttribute("style"))),
  ).toEqual(comparisons);

  // Focusing/leaving the field must not turn an unchanged preset into Custom.
  await rings.focus();
  await rings.press("Tab");
  await expect(selector).toHaveValue("sram-rival-xplr-e1");
  await rings.fill("42");
  await rings.press("Tab");
  await ready(page);
  await expect(selector).toHaveValue("custom");
  await expect(page.getByTestId("gearing-preset")).toHaveCount(0);
  await selector.selectOption("shimano-tiagra-r4000");
  await ready(page);
  await expect(rings).toHaveValue("34, 50");
  await expect(cogs).toHaveValue("11, 13, 15, 17, 19, 21, 23, 25, 28, 32, 36");
  await cogs.fill("11, 15, 20, 28, 36");
  await cogs.press("Enter");
  await ready(page);
  await expect(selector).toHaveValue("custom");
  await cogs.fill("11, 11, 36");
  await cogs.press("Enter");
  await expect(page.getByRole("alert")).toContainText("Cassette");
  await selector.selectOption("sram-apex-xplr");
  await ready(page);
  await expect(rings).toHaveValue("40");
  await expect(cogs).toHaveValue(
    "11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 44",
  );
  await page.getByRole("button", { name: "Reset ride inputs" }).click();
  await ready(page);
  await expect(selector).toHaveValue("shimano-105-r7100");
  await expect(rings).toHaveValue("34, 50");
  await expect(cogs).toHaveValue(
    "11, 12, 13, 14, 15, 17, 19, 21, 24, 27, 30, 34",
  );
});

test("presets and sources are accessible in both languages, fit narrow screens and export actual gearing", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?lang=cs");
  await ready(page, true);
  await page
    .locator("summary")
    .filter({ hasText: "Převody a kadence" })
    .click();
  await page
    .getByLabel("Přednastavená sada", { exact: true })
    .selectOption("sram-force-xplr-e1");
  await ready(page, true);
  await page.getByText("Specifikace výrobce", { exact: true }).click();
  await expect(page.getByTestId("gearing-preset")).toContainText("42 zubů");
  await expect(page.getByTestId("gearing-preset")).toContainText("10–46 zubů");
  const links = await page
    .locator(".gearing-sources a")
    .evaluateAll((els) => els.map((e) => (e as HTMLAnchorElement).href));
  expect(links).toEqual([
    "https://www.sram.com/en/service/models/fc-frc-1w-e1",
    "https://www.sram.com/en/service/models/cs-xg-1371-e1",
    "https://www.sram.com/en/service/models/rd-frc-1e-e1",
  ]);
  await page.locator(".groupset-picker").screenshot({
    path: `test-results/${info.project.name}-groupset-czech.png`,
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);

  await page.getByLabel("Jazyk", { exact: true }).selectOption("en");
  await expect(page.getByLabel("Groupset preset", { exact: true })).toHaveValue(
    "sram-force-xplr-e1",
  );
  await expect(page.getByTestId("gearing-preset")).toContainText("42 teeth");
  await expect(
    page.getByText("Manufacturer specifications", { exact: true }),
  ).toBeVisible();
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download ride briefing" }).click();
  const file = await downloaded;
  const content = await readFile((await file.path())!, "utf8");
  expect(content).toContain("Front chainrings: 42");
  expect(content).toContain(
    "Cassette cogs: 10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 46",
  );

  // The longest preset label and open source list must stay inside a small phone.
  await page.setViewportSize({ width: 320, height: 800 });
  await page
    .getByLabel("Groupset preset", { exact: true })
    .selectOption("shimano-grx-rx820-1x51");
  await ready(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await expect(page.getByTestId("gearing-preset")).toContainText(
    "GRX RX820 · 1×12 · 10–51",
  );
  expect(errors).toEqual([]);
});
