import client from './client';

export interface User {
  id: string;
  username: string;
  role: string;
  created_at?: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function register(username: string, password: string): Promise<AuthResponse> {
  const res = await client.post('/api/auth/register', { username, password });
  return res.data;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const res = await client.post('/api/auth/login', { username, password });
  return res.data;
}

export async function logout(refreshToken: string): Promise<void> {
  await client.post('/api/auth/logout', { refresh_token: refreshToken });
}

export async function refreshToken(refreshToken: string): Promise<{ access_token: string; refresh_token: string }> {
  const res = await client.post('/api/auth/refresh', { refresh_token: refreshToken });
  return res.data;
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await client.put('/api/auth/password', { old_password: oldPassword, new_password: newPassword });
}

export async function getMe(): Promise<User> {
  const res = await client.get('/api/auth/me');
  return res.data;
}
