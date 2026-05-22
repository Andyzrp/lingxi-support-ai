import request from './request'

export const productApi = {
  // GET /api/v1/products [1]
  getList: (params) => request.get('/products', { params }),

  // GET /api/v1/products/categories [1]
  getCategories: () => request.get('/products/categories'),

  // GET /api/v1/products/{id} [1]
  getDetail: (id) => request.get(`/products/${id}`),
}