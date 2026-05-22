import request from './request'

export const orderApi = {
  // POST /api/v1/orders [1]
  create: (data) => request.post('/orders', data),

  // GET /api/v1/orders [1]
  getMyList: (params) => request.get('/orders', { params }),

  // GET /api/v1/orders/{order_no} [1]
  getDetail: (orderNo) => request.get(`/orders/${orderNo}`),

  // GET /api/v1/orders/{order_no}/logistics [1]
  getLogistics: (orderNo) => request.get(`/orders/${orderNo}/logistics`),

  // POST /api/v1/orders/refund [1]
  applyRefund: (data) => request.post('/orders/refund', data),
}