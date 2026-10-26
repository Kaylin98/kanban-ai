import { expect, test } from "@playwright/test";
import { defaultBoard } from "../src/test/board";
import { PASSWORD, USERNAME } from "./credentials";

test.beforeEach(async ({ page }) => {
  await page.request.post("/api/login", {
    data: { username: USERNAME, password: PASSWORD },
  });
  await page.request.put("/api/board", { data: defaultBoard });
});

test("sends a chat message and shows the reply and the updated board", async ({ page }) => {
  const board = {
    columns: defaultBoard.columns.map((column) =>
      column.id === "col-backlog" ? { ...column, cardIds: [...column.cardIds, "card-ai"] } : column
    ),
    cards: { ...defaultBoard.cards, "card-ai": { id: "card-ai", title: "Write release notes", details: "" } },
  };
  let request: unknown;
  await page.route("**/api/chat", async (route) => {
    request = route.request().postDataJSON();
    await route.fulfill({ json: { reply: "Added Write release notes to Backlog.", board } });
  });

  await page.goto("/");
  // The chat starts minimized to a bubble.
  await page.getByRole("button", { name: "Open AI assistant" }).click();
  await page.getByLabel("Message", { exact: true }).fill("Add a card called Write release notes to Backlog");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Added Write release notes to Backlog.")).toBeVisible();
  await expect(page.getByTestId("column-col-backlog").getByTestId("card-card-ai")).toBeVisible();
  expect(request).toEqual({
    message: "Add a card called Write release notes to Backlog",
    history: [],
  });
});
