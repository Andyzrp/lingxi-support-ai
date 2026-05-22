/**
 * 应用全局配置
 * 系统名称、Logo、favicon 统一在这里维护
 * 所有组件从此文件读取，不硬编码
 */
const appConfig = {
  // ── 系统基础信息 ──────────────────────────
  systemName:     '灵犀智能商城',
  systemNameFull: '灵犀智能客服系统',
  systemNameEn:   'Lingxi Support AI',
  companyName:    '灵犀科技',
  version:        'v1.0.0',

  // ── 页面标题后缀 ──────────────────────────
  titleSuffix: ' - 灵犀商城',
  titleSuffixAdmin: ' - 灵犀智能客服后台',

  // ── 品牌 Logo 路径 ────────────────────────
  // public/brand/ 目录下的文件
  // Vite 中 public/ 是根目录，代码里写 /brand/ 即可
  logo: {
	// 灵犀客服（后台管理用）
    loginLight: '/brand/lingxi-login-logo-light.svg',
    loginDark:  '/brand/lingxi-login-logo-dark.svg',
    adminLight: '/brand/lingxi-admin-logo-light.svg',
    adminDark:  '/brand/lingxi-admin-logo-dark.svg',
	
	// 灵犀商城（前台商城用）
	mallLogo:    '/brand/lingxi-mall-logo.svg',
	mallLogoDark:'/brand/lingxi-mall-logo-dark.svg',
	mallHeader:  '/brand/lingxi-mall-header-logo.svg',
	mallIcon:    '/brand/lingxi-mall-icon.svg',
	mallMono:    '/brand/lingxi-mall-logo-mono.svg',
	
	// 客服悬浮按钮
    chatButton: '/brand/lingxi-chat-button.svg',
  },

  // ── Favicon 路径 ──────────────────────────
  // 在 index.html 中通过 %VITE_XXX% 环境变量读取
  favicon: {
    svg:        '/brand/favicon.svg',
    png32:      '/brand/favicon-32x32.png',
    png16:      '/brand/favicon-16x16.png',
    appleTouch: '/brand/apple-touch-icon.png',
  },

  // ── 版权信息 ──────────────────────────────
  copyright: '© 2026 灵犀智能客服系统',
  techTags:  ['DeepSeek', 'LangGraph', 'Qdrant'],

  // ── 客服 WebSocket 配置 [1] ───────────────
  chat: {
    channelToken: 'LrDSr5ZRFjCu0mBunFxOTiMTTVeZ8m7xCJhqygIfHmw',
    welcomeMsg:   '您好！我是灵犀客服 😊 请问有什么可以帮您？',
  },
}

export default appConfig