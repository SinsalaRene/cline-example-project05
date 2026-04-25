# Build stage
FROM node:18-alpine AS build

WORKDIR /app

COPY package.json angular.json tsconfig.json ./
RUN npm install

COPY src/ ./src/
COPY dist/ ./dist/

RUN npm run build -- --configuration production

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist/ /usr/share/nginx/html/

# Copy nginx config if needed
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]