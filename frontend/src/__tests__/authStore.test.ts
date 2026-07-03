/** 测试 authStore — 认证状态管理 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock localStorage
const localStorageStore: Record<string, string> = {};
const localStorageMock = {
  getItem: vi.fn((key: string) => localStorageStore[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { localStorageStore[key] = value; }),
  removeItem: vi.fn((key: string) => { delete localStorageStore[key]; }),
  clear: vi.fn(() => { Object.keys(localStorageStore).forEach(k => delete localStorageStore[k]); }),
  get length() { return Object.keys(localStorageStore).length; },
  key: vi.fn((index: number) => Object.keys(localStorageStore)[index] ?? null),
};

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });

// Mock API module — must be before dynamic imports
const mockLogin = vi.fn();
const mockRegister = vi.fn();
const mockLogout = vi.fn();
const mockGetMe = vi.fn();

vi.mock('../api/auth', () => ({
  login: (...args: any[]) => mockLogin(...args),
  register: (...args: any[]) => mockRegister(...args),
  logout: (...args: any[]) => mockLogout(...args),
  getMe: (...args: any[]) => mockGetMe(...args),
}));

// Dynamic import so vi.mock is hoisted properly
let useAuthStore: typeof import('../stores/authStore').useAuthStore;

beforeAll(async () => {
  const mod = await import('../stores/authStore');
  useAuthStore = mod.useAuthStore;
});

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.keys(localStorageStore).forEach(k => delete localStorageStore[k]);
    if (useAuthStore) {
      useAuthStore.setState({ user: null, loading: true });
    }
  });

  describe('fetchUser', () => {
    it('没有 token 时应设置 loading=false, user=null', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      await useAuthStore.getState().fetchUser();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.loading).toBe(false);
    });

    it('有 token 且 API 正常时应该获取用户信息', async () => {
      const mockUser = { id: '1', username: 'testuser', role: 'user' };
      localStorageMock.getItem.mockReturnValue('fake-access-token');
      mockGetMe.mockResolvedValue(mockUser);

      await useAuthStore.getState().fetchUser();

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.loading).toBe(false);
      expect(mockGetMe).toHaveBeenCalledTimes(1);
    });

    it('有 token 但 API 失败时应清除 token 并设置 user=null', async () => {
      localStorageMock.getItem.mockReturnValue('expired-token');
      mockGetMe.mockRejectedValue(new Error('Unauthorized'));

      await useAuthStore.getState().fetchUser();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.loading).toBe(false);
      expect(localStorageMock.clear).toHaveBeenCalled();
    });
  });

  describe('login', () => {
    it('登录成功应保存 token 并设置 user', async () => {
      const mockUser = { id: '2', username: 'admin', role: 'admin' };
      mockLogin.mockResolvedValue({
        user: mockUser,
        access_token: 'access-123',
        refresh_token: 'refresh-456',
      });

      await useAuthStore.getState().login('admin', '123456');

      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'access-123');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'refresh-456');

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
    });

    it('登录失败应抛出异常', async () => {
      mockLogin.mockRejectedValue(new Error('用户名或密码错误'));

      await expect(
        useAuthStore.getState().login('admin', 'wrong')
      ).rejects.toThrow('用户名或密码错误');
    });
  });

  describe('register', () => {
    it('注册成功应保存 token 并设置 user', async () => {
      const mockUser = { id: '3', username: 'newuser', role: 'user' };
      mockRegister.mockResolvedValue({
        user: mockUser,
        access_token: 'access-new',
        refresh_token: 'refresh-new',
      });

      await useAuthStore.getState().register('newuser', 'password123');

      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'access-new');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'refresh-new');

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
    });
  });

  describe('logout', () => {
    it('退出登录应清除 localStorage 和 user', async () => {
      useAuthStore.setState({
        user: { id: '1', username: 'test', role: 'user' },
        loading: false,
      });
      localStorageMock.getItem.mockReturnValue('refresh-token');

      await useAuthStore.getState().logout();

      expect(mockLogout).toHaveBeenCalledWith('refresh-token');
      expect(localStorageMock.clear).toHaveBeenCalled();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
    });

    it('没有 refresh_token 时退出也应清除状态', async () => {
      useAuthStore.setState({
        user: { id: '1', username: 'test', role: 'user' },
        loading: false,
      });
      localStorageMock.getItem.mockReturnValue(null);

      await useAuthStore.getState().logout();

      expect(localStorageMock.clear).toHaveBeenCalled();
      expect(useAuthStore.getState().user).toBeNull();
    });
  });
});
