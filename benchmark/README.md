# Benchmark: gRPC vs REST

Este diretório contém o script de teste de carga concorrente utilizando o **k6** para comparar o desempenho da comunicação interna via gRPC vs REST.

O cliente (HClient) ataca o Gateway P através de rotas HTTP distintas para cada protocolo:
- `/api/v1/livros`: O Gateway P usa **gRPC** para comunicar com o Microsserviço A.
- `/api/v2/livros`: O Gateway P usa **REST** para comunicar com o Microsserviço A-REST.

Para garantir uma comparação arquiteturalmente justa e que não sofra com gargalos intrínsecos a threads (como o Global Interpreter Lock - GIL - do Python), os microsserviços de destino utilizam um modelo **totalmente assíncrono**:
- O Serviço A (gRPC) utiliza **gRPC Assíncrono (`grpc.aio`)** com o driver não-bloqueante `asyncpg` para o PostgreSQL.
- O Serviço A-REST utiliza o framework assíncrono **FastAPI** também com o driver `asyncpg`.

Dessa forma, isolamos cientificamente o impacto do protocolo interno (gRPC vs REST) mantendo as camadas de banco de dados e execução idênticas.

## Pré-requisitos

Instale o k6 de acordo com o seu sistema operacional:
https://k6.io/docs/get-started/installation/

## Executando o Benchmark

As imagens e a infraestrutura estão preparadas para rodar no Kubernetes (Kind/Minikube).

1. **Subir a infraestrutura:**
   Na raiz do projeto, inicie o cluster e o deploy:
   ```bash
   ./run.sh
   ```
   *Nota: Este script inicializa o banco de dados, cria o namespace e aguarda que o CDC (Debezium) faça a sincronização inicial para o Elasticsearch. Todos os pods estarão prontos ao final.*

2. **Rodar os Testes de Carga:**
   Execute o script unificado que verifica a saúde das rotas, faz o port-forward automático do Gateway e roda o k6:
   ```bash
   ./run-benchmark.sh
   ```

3. **Reconstruindo Imagens (Para Desenvolvimento):**
   Caso você altere o código de algum microsserviço, utilize a flag `--build`. Isso forçará a construção das imagens Docker localmente e fará o carregamento para o cluster Kind antes da execução do teste:
   ```bash
   ./run-benchmark.sh --build
   ```

## Analisando os Resultados

O k6 exibirá um relatório final no terminal comparando as tags `protocol:grpc` e `protocol:rest`, com métricas como:
- `http_req_duration`: Latência P50, P90 e P95
- `http_reqs`: Throughput total (requisições por segundo)
- **Thresholds**: Ambos os protocolos têm um limite configurado de aprovação (p95 < 500ms).
