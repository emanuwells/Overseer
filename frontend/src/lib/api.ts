import { apiToken } from './config';

export async function api<T>(path: string): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  const token = apiToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { headers });
  if (response.status === 401) throw new Error('API devolveu 401. Confirma o token.');
  if (!response.ok) throw new Error(`API devolveu HTTP ${response.status}.`);
  return response.json() as Promise<T>;
}
