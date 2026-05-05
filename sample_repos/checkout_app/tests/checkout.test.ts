import { trackCheckoutStarted } from "../src/analytics";

test("trackCheckoutStarted is callable", () => {
  expect(typeof trackCheckoutStarted).toBe("function");
});
