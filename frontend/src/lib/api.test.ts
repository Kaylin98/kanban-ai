import { sendChat, type ChatMessage } from "@/lib/api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("sendChat", () => {
  it("sends only the last 20 history messages, which is what the server accepts", async () => {
    const fetch = vi.fn(async () => Response.json({ reply: "Hi.", board: null }));
    vi.stubGlobal("fetch", fetch);
    const history: ChatMessage[] = Array.from({ length: 25 }, (_, i) => ({
      role: i % 2 ? "assistant" : "user",
      content: `message ${i}`,
    }));

    await sendChat("Hello", history);

    const body = JSON.parse(fetch.mock.calls[0][1].body);
    expect(body.history).toEqual(history.slice(5));
  });
});
