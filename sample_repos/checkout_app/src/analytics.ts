import { trackEvent, rateLimit } from "analytics-sdk";

export function trackCheckoutStarted(userId: string) {
  trackEvent("checkout_started", { userId });
}

export function getAnalyticsRateLimit() {
  return rateLimit();
}
