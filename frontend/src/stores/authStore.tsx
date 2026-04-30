import { useReducer, useEffect, type ReactNode } from 'react';
import { authApi } from '../api/auth';
import type { User } from '../api/types';
import { AuthContext, type AuthState } from './authContext';

type AuthAction =
  | { type: 'SET_USER'; user: User; token: string }
  | { type: 'UPDATE_USER'; user: User }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; loading: boolean };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_USER':
      return { user: action.user, token: action.token, loading: false };
    case 'UPDATE_USER':
      return { ...state, user: action.user };
    case 'LOGOUT':
      return { user: null, token: null, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: action.loading };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    token: localStorage.getItem('access_token'),
    loading: true,
  });

  // 앱 시작 시 저장된 토큰으로 사용자 정보 복원
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      dispatch({ type: 'SET_LOADING', loading: false });
      return;
    }
    authApi
      .me()
      .then((user) => dispatch({ type: 'SET_USER', user, token }))
      .catch(() => {
        localStorage.removeItem('access_token');
        dispatch({ type: 'LOGOUT' });
      });
  }, []);

  const setUser = (user: User) => {
    dispatch({ type: 'UPDATE_USER', user });
  };

  const login = (token: string, user: User) => {
    localStorage.setItem('access_token', token);
    dispatch({ type: 'SET_USER', user, token });
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem('access_token');
      dispatch({ type: 'LOGOUT' });
    }
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}
