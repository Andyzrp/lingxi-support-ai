import request from './request'

export const authApi = {
  // POST /api/v1/auth/register [1]
  register: (data) => request.post('/auth/register', data),

  // POST /api/v1/auth/login [1]
  login: (data) => request.post('/auth/login', data),

  // GET /api/v1/auth/me [1]
  getMe: () => request.get('/auth/me'),

  // PUT /api/v1/auth/me [1]
  updateMe: (data) => request.put('/auth/me', data),

  // PUT /api/v1/auth/me/password [1]
  updatePassword: (data) => request.put('/auth/me/password', data),
}