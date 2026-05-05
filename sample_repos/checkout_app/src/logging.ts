import { createLogger } from "logging-lib";

const logger = createLogger({ service: "checkout-web-app" });

export function logCheckoutEvent(eventName: string, payload: Record<string, unknown>) {
  logger.info(eventName, payload);
}
