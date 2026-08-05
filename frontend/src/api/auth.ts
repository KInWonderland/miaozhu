import client from './client'

export interface AuthUser {
  username: string
}

export interface LoginPayload {
  username: string
  password: string
}

export function login(payload: LoginPayload) {
  return client.post<AuthUser>('/auth/login', payload, {
    skipAuthRedirect: true,
    silentError: true,
  })
}

export function getCurrentUser() {
  return client.get<AuthUser>('/auth/me', {
    skipAuthRedirect: true,
    silentError: true,
  })
}

export function logout() {
  return client.post('/auth/logout')
}
