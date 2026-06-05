export function getStoredAccessToken() {
  return localStorage.getItem("access_token") ?? localStorage.getItem("accessToken") ?? undefined;
}
