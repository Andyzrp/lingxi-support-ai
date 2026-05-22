import request from './request'

export const chatApi = {
  // POST /api/v1/chat/conversations/{id}/evaluate [1]
  evaluate: (conversationId, data) =>
    request.post(`/chat/conversations/${conversationId}/evaluate`, data),

  // GET /api/v1/chat/conversations/{id}/messages
  getMessages: (conversationId) =>
    request.get(`/chat/conversations/${conversationId}/messages`),
}