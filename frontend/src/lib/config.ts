export function apiToken(): string {
  const fromConfig = window.OVERSEER_CONFIG?.apiToken;
  if (fromConfig) return String(fromConfig);
  return sessionStorage.getItem('overseer_api_token') || '';
}

export function hasApiToken(): boolean {
  return Boolean(apiToken());
}
