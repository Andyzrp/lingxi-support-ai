<template>
  <router-view />

  <!-- 客服悬浮组件：全局挂载，登录后可见（/chat 独立聊天页除外）-->
  <ChatWidget v-if="userStore.isLoggedIn && !isChatPage" />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import ChatWidget from '@/components/chat/ChatWidget.vue'

const route    = useRoute()
const userStore = useUserStore()
const isChatPage = computed(() => route.path.startsWith('/chat'))

onMounted(() => {
  userStore.init()
})
</script>