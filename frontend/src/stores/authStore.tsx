'use client';

import { useReducer, useEffect, type ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { authApi } from '../api/auth';
import type { User } from '../api/types';
import { AuthContext, type AuthState } from './authContext';

type AuthAction =
  | { type: 'SET_USER'; user: User }
  | { type: 'UPDATE_USER'; user: User }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; loading: boolean };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_USER':
      return { user: action.user, loading: false };
    case 'UPDATE_USER':
      return { ...state, user: action.user };
    case 'LOGOUT':
      return { user: null, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: action.loading };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    loading: true,
  });

  // 앱 시작 시 쿠키 기반으로 세션 복원
  useEffect(() => {
    const init = async () => {
      const isPublicAuthPage =
        pathname === '/login' ||
        pathname === '/company/login' ||
        pathname === '/signup';
      if (isPublicAuthPage) {
        dispatch({ type: 'LOGOUT' });
        return;
      }
      try {
        const user = await authApi.me();
        dispatch({ type: 'SET_USER', user });
      } catch {
        // Access Token 만료 → Refresh 시도
        try {
          const res = await authApi.refresh();
          dispatch({ type: 'SET_USER', user: res.user });
        } catch {
          dispatch({ type: 'LOGOUT' });
        }
      }
    };
    init();
  }, [pathname]);

  const setUser = (user: User) => {
    dispatch({ type: 'UPDATE_USER', user });
  };

  const login = (user: User) => {
    dispatch({ type: 'SET_USER', user });
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}
