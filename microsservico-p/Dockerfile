FROM golang:1.22-alpine AS builder
WORKDIR /app

RUN apk add --no-cache protobuf protobuf-dev && \
    go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.34.1 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.4.0

COPY microsservico-p/go.mod ./
RUN go mod download || true

# Gera os stubs Go a partir do .proto
COPY proto/biblioteca.proto ./proto/
RUN protoc \
      --go_out=./proto --go_opt=paths=source_relative \
      --go-grpc_out=./proto --go-grpc_opt=paths=source_relative \
      -I./proto \
      ./proto/biblioteca.proto

COPY microsservico-p/*.go ./
RUN go mod tidy && CGO_ENABLED=0 GOOS=linux go build -o server .

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/server .
ENV HTTP_PORT=8080
ENV SERVICE_A_ADDR=microsservico-a:50051
EXPOSE 8080
CMD ["./server"]
