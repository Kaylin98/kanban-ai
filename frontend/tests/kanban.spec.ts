import { expect, test, type Page } from "@playwright/test";
import { defaultBoard } from "../src/test/board";
import { PASSWORD, USERNAME } from "./credentials";

const cardIds = (page: Page, columnId: string) =>
  page
    .getByTestId(columnId)
    .locator('[data-testid^="card-"]')
    .evaluateAll((cards) => cards.map((card) => card.getAttribute("data-testid")));

// Drags a card by its center to a point offset from the bottom-center of another element.
const dragTo = async (page: Page, cardTestId: string, targetTestId: string, offsetY: number) => {
  const from = await page.getByTestId(cardTestId).boundingBox();
  const to = await page.getByTestId(targetTestId).boundingBox();
  if (!from || !to) {
    throw new Error("Unable to resolve drag coordinates.");
  }
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(to.x + to.width / 2, to.y + to.height + offsetY, { steps: 20 });
};

// Resolves when the board has been saved. Start waiting before the change.
const boardSaved = (page: Page) =>
  page.waitForResponse(
    (response) => response.url().endsWith("/api/board") && response.request().method() === "PUT"
  );

// page.request shares the browser context's cookies, so this signs the page in.
// The board is stored on the server, so reset it to the default before each test.
test.beforeEach(async ({ page }) => {
  await page.request.post("/api/login", {
    data: { username: USERNAME, password: PASSWORD },
  });
  await page.request.put("/api/board", { data: defaultBoard });
});

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("edits a card", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  await card.getByRole("button", { name: /edit align roadmap themes/i }).click();
  await card.getByLabel("Card title").fill("Edited via e2e");
  await card.getByLabel("Card details").fill("New details.");
  await card.getByRole("button", { name: /save/i }).click();
  await expect(card.getByText("Edited via e2e")).toBeVisible();
  await expect(card.getByText("New details.")).toBeVisible();
});

test("deletes a card", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  await card.getByRole("button", { name: /delete align roadmap themes/i }).click();
  await expect(card).toHaveCount(0);
});

test("renames a column", async ({ page }) => {
  await page.goto("/");
  const input = page.getByTestId("column-col-backlog").getByLabel("Column title");
  await input.fill("Ideas");
  await expect(input).toHaveValue("Ideas");
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("keeps every change after a reload", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1000 });
  await page.goto("/");

  let saved = boardSaved(page);
  await page.getByTestId("column-col-backlog").getByLabel("Column title").fill("Ideas");
  await saved;

  const backlog = page.getByTestId("column-col-backlog");
  await backlog.getByRole("button", { name: /add a card/i }).click();
  await backlog.getByPlaceholder("Card title").fill("Persisted card");
  await backlog.getByPlaceholder("Details").fill("Still here.");
  saved = boardSaved(page);
  await backlog.getByRole("button", { name: /add card/i }).click();
  await saved;

  const card = page.getByTestId("card-card-2");
  await card.getByRole("button", { name: /edit gather customer signals/i }).click();
  await card.getByLabel("Card title").fill("Edited and saved");
  saved = boardSaved(page);
  await card.getByRole("button", { name: /save/i }).click();
  await saved;

  saved = boardSaved(page);
  await page.getByTestId("card-card-6").getByRole("button", { name: /delete/i }).click();
  await saved;

  saved = boardSaved(page);
  await dragTo(page, "card-card-1", "card-card-7", 20);
  await page.mouse.up();
  await saved;

  await page.reload();
  await expect(page.getByTestId("column-col-backlog").getByLabel("Column title")).toHaveValue("Ideas");
  await expect(backlog.getByText("Persisted card")).toBeVisible();
  await expect(page.getByTestId("card-card-2").getByText("Edited and saved")).toBeVisible();
  await expect(page.getByTestId("card-card-6")).toHaveCount(0);
  expect(await cardIds(page, "column-col-done")).toEqual(["card-card-7", "card-card-1", "card-card-8"]);
});

test.describe("drop position", () => {
  // Large enough that every drop target is inside the viewport.
  test.use({ viewport: { width: 1600, height: 1000 } });

  test("drops a card below the last card of another column", async ({ page }) => {
    await page.goto("/");
    await dragTo(page, "card-card-1", "card-card-6", 40);
    await page.mouse.up();
    expect(await cardIds(page, "column-col-review")).toEqual(["card-card-6", "card-card-1"]);
  });

  test("drops a card between two cards of another column", async ({ page }) => {
    await page.goto("/");
    await dragTo(page, "card-card-1", "card-card-4", 20);
    await page.mouse.up();
    expect(await cardIds(page, "column-col-progress")).toEqual([
      "card-card-4",
      "card-card-1",
      "card-card-5",
    ]);
  });

  test("drops a card on the lower half of the last card after it", async ({ page }) => {
    await page.goto("/");
    await dragTo(page, "card-card-3", "card-card-8", -8);
    await page.mouse.up();
    expect(await cardIds(page, "column-col-done")).toEqual([
      "card-card-7",
      "card-card-8",
      "card-card-3",
    ]);
  });

  test("escape cancels a drag and restores the board", async ({ page }) => {
    await page.goto("/");
    await dragTo(page, "card-card-1", "card-card-6", 40);
    await page.keyboard.press("Escape");
    await page.mouse.up();
    expect(await cardIds(page, "column-col-backlog")).toEqual(["card-card-1", "card-card-2"]);
    expect(await cardIds(page, "column-col-review")).toEqual(["card-card-6"]);
  });
});
