import { fetchUser } from "profile-sdk";

export async function loadProfile(userId: string) {
  const profile = await fetchUser(userId);
  return profile;
}
