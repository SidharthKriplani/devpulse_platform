import { authenticate } from "auth-sdk";

export async function loginUser(apiKey: string) {
  const session = await authenticate(apiKey);
  return session;
}
