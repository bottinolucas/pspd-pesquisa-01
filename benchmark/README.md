# Benchmark: gRPC vs REST

Este diretório contém o script de teste de carga concorrente utilizando o **k6** para comparar o desempenho da comunicação interna via gRPC vs REST.

O cliente (HClient) ataca o Gateway P através de requisições HTTP idênticas. A diferença reside na rota:
- `/api/v1/livros`: O Gateway P usa **gRPC** para comunicar com o Microsserviço A.
- `/api/v2/livros`: O Gateway P usa **REST** para comunicar com o Microsserviço A-REST.

Dessa forma, isolamos cientificamente o impacto do protocolo interno.

## Pré-requisitos

Instale o k6 de acordo com o seu sistema operacional:
https://k6.io/docs/get-started/installation/

## Como Executar (Local via Docker Compose)

Com o projeto rodando via `docker compose up -d`, execute:

```bash
k6 run benchmark/grpc_vs_rest.js
```

## Como Executar (Kubernetes)

1. Faça o port-forward do Gateway P:
```bash
kubectl port-forward svc/microsservico-p 8080:8080 -n biblioteca
```

2. Em outro terminal, execute o k6 apontando para o Gateway:
```bash
k6 run --env GATEWAY_URL=http://localhost:8080 benchmark/grpc_vs_rest.js
```

3. (Opcional) Acompanhe o consumo de recursos dos pods em tempo real:
```bash
watch kubectl top pods -n biblioteca
```

## Analisando os Resultados

O k6 exibirá um relatório final no terminal comparando as tags `protocol:grpc` e `protocol:rest`, incluindo:
- `http_req_duration`: Latência P50, P95, e P99
- `http_reqs`: Throughput total (requisições por segundo)
