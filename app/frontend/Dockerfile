FROM node:23-alpine3.21 AS build
RUN apk update && apk add --no-cache bash make
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --production
COPY . .
RUN yarn build

FROM nginx:1.27-alpine3.21
COPY --from=build /app/build /usr/share/nginx/html
COPY config/nginx.conf /etc/nginx/nginx.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
