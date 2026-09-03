# ==================== 前端静态托管 ====================
# 说明:dist/ 由容器内构建产出并 docker cp 到本目录
# (Windows + Docker Desktop 下 BuildKit/bind-mount 里跑 npm ci 不稳定:
#  package-lock.json 曾指向公司内网镜像 mirrors.djicorp.com,本地 ENOTFOUND)
# 重新构建 dist 的流程:
#   docker run -d --name fe_build -w /app node:20-slim sleep 3600
#   docker cp frontend/. fe_build:/app/
#   docker exec fe_build sh -c "cd /app && sed -i 's#http[s]*://[^/\"]*/registry/#https://registry.npmmirror.com/#g' package-lock.json && npm config set registry https://registry.npmmirror.com && npm ci --no-audit --no-fund && npm run build"
#   docker cp fe_build:/app/dist frontend/dist && docker rm -f fe_build
FROM nginx:alpine

# 内联最小化 nginx 配置:监听 3000(与 docker-compose 端口映射一致)+ Vue Router history 模式 fallback
RUN <<EOF
cat > /etc/nginx/conf.d/default.conf <<'NGINX'
server {
    listen       3000;
    server_name  _;
    root         /usr/share/nginx/html;
    index        index.html;

    # index.html 不缓存，确保每次获取最新版本
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        expires off;
    }

    # 带哈希的静态资源长期缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX
EOF

# 拷贝预构建的静态产物
COPY dist /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
