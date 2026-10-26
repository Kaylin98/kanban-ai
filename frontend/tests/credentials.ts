// The local test server is started with these (see playwright.config.ts). To test a
// running container (BASE_URL), set E2E_USERNAME and E2E_PASSWORD to its credentials.
export const USERNAME = process.env.E2E_USERNAME ?? "test-user";
export const PASSWORD = process.env.E2E_PASSWORD ?? "test-password";
