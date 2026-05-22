import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', {
  state: () => ({
    // 格式：{ productId: { product, quantity } }
    items: {},
  }),

  getters: {
    totalCount: (state) =>
      Object.values(state.items).reduce((sum, item) => sum + item.quantity, 0),

    totalPrice: (state) =>
      Object.values(state.items).reduce(
        (sum, item) => sum + item.product.price * item.quantity,
        0
      ),

    isEmpty: (state) => Object.keys(state.items).length === 0,
  },

  actions: {
    addItem(product, quantity = 1) {
      const id = product.id
      if (this.items[id]) {
        this.items[id].quantity += quantity
      } else {
        this.items[id] = { product, quantity }
      }
    },

    removeItem(productId) {
      delete this.items[productId]
    },

    clear() {
      this.items = {}
    },
  },
})