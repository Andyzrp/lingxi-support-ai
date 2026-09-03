# syntax=docker/dockerfile:1.7

# ==================== 构建阶段 ====================
FROM node:20-alpine AS builder

WORKDIR /app

# 利用 Docker 缓存：先装依赖（仅当依赖变化时才重新安装）
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码并构建生产产物（输出到 dist/）
COPY . .
RUN npm run build

# ==================== 运行阶段：nginx 托管 SPA 静态产物 ====================
FROM nginx:alpine

# 内联一份最小化 nginx 配置：监听 3000（与 docker-compose 端口映射一致）+ Vue Router history 模式 fallback
RUN <<EOF
cat > /etc/nginx/conf.d/default.conf <<'NGINX'
server {
    listen       3000;
    server_name  _;
    root         /usr/share/nginx/html;
    index        index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX
EOF

# 拷贝构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
