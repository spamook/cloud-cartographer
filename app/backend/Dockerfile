FROM golang:1.24-alpine3.21 AS build
RUN apk add --no-cache make
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN make build


FROM alpine:3.21
WORKDIR /app
COPY --from=build /app/cmd/main /cmd/main
COPY --from=build /app/.env /.env
COPY --from=build /app/packages/db/migrations/ /packages/db/migrations/
EXPOSE 8080
CMD [ "/cmd/main" ]
