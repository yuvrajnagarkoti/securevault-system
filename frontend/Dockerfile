# Frontend Dockerfile for SecureVault
FROM nginx:alpine

# Copy custom nginx config (disables caching for dev)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend files
COPY index.html /usr/share/nginx/html/
COPY index.js /usr/share/nginx/html/
COPY styles/ /usr/share/nginx/html/styles/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
