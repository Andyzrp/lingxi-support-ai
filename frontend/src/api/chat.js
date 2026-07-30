import request from './request'

export const chatApi = {
  // POST /api/v1/chat/evaluate?conversation_id=...
  evaluate: (conversationId, data) =>
    request.post(`/chat/evaluate?conversation_id=${conversationId}`, data),

  // GET /api/v1/chat/conversations/{id}/messages
  getMessages: (conversationId) =>
    request.get(`/chat/conversations/${conversationId}/messages`),
}