import { create } from 'zustand';
import type { User } from '../api/auth';
import * as authApi from '../api/auth';

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,

  login: async (username, password) => {
    const res = await authApi.login(username, password);
    localStorage.setItem('access_token', res.access_token);
    localStorage.setItem('refresh_token', res.refresh_token);
    set({ user: res.user });
  },

  register: async (username, password) => {
    const res = await authApi.register(username, password);
    localStorage.setItem('access_token', res.access_token);
    localStorage.setItem('refresh_token', res.refresh_token);
    set({ user: res.user });
  },

  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try { await authApi.logout(refreshToken); } catch {}
    }
    localStorage.clear();
    set({ user: null });
  },

  fetchUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ user: null, loading: false });
      return;
    }
    try {
      const user = await authApi.getMe();
      set({ user, loading: false });
    } catch {
      localStorage.clear();
      set({ user: null, loading: false });
    }
  },
}));
