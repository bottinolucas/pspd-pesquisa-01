# Biblioteca Distribuída

Aplicação distribuída com arquitetura gRPC — trabalho prático de Programacao para Sistemas Paralelos e Distribuídos (UnB).

## Arquitetura

```
[Browser/k6] ──HTTP──► [Frontend / API Gateway :8080]
                             │
                        /api/v1/* (gRPC) ou /api/v2/* (REST)
                             │
                     [P: Go/Gin :8080]  ← API Gateway
                      │            │
         ┌── gRPC ────┤            ├──── gRPC ──┐
         │            │            │            │
         ▼            ▼            ▼            ▼
   [A: Python]   [A-REST: Py]   [B: Java]   [B: Java REST]
   gRPC :50051   REST :5001     gRPC:50052  REST :8081
   Catálogo      Catálogo       Estoque     Estoque
         │            │            │            │
         └─────┬──────┘            └──────┬─────┘
               │                          │
       [PostgreSQL :5432]          [Elasticsearch]
```

---

## Pré-requisitos (Instalação)

Para rodar este projeto, você precisará das seguintes ferramentas de infraestrutura instaladas na sua máquina:

1. **Docker & Docker Compose**: Utilizado para virtualização dos containers.
   - [Instalar Docker Desktop (Windows/Mac)](https://docs.docker.com/get-docker/)
   - [Instalar Docker Engine (Linux)](https://docs.docker.com/engine/install/)
   - *(Linux)*: Lembre-se de [configurar o Docker para rodar sem sudo](https://docs.docker.com/engine/install/linux-postinstall/).

2. **Kubernetes via Kind**: `kind` (Kubernetes in Docker) permite rodar clusters locais de forma extremamente leve usando containers Docker como nós do cluster.
   - [Instalar o Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)

3. **kubectl**: A ferramenta de linha de comando para interagir com clusters Kubernetes.
   - [Instalar o kubectl](https://kubernetes.io/docs/tasks/tools/)

4. **k6 (Apenas para Benchmark)**: Ferramenta de teste de carga moderna.
   - [Instalar o k6](https://k6.io/docs/get-started/installation/)

---

## Rodar o Projeto com Kubernetes (Recomendado)

O projeto foi projetado para rodar em um cluster Kubernetes. Todos os manifestos e configurações de volume estão em `k8s/`.

Existe um script facilitador (`run.sh`) que cria o cluster Kind (caso não exista), configura o namespace `biblioteca`, aplica todos os manifestos e lida com a sincronização do banco de dados (Postgres e Elasticsearch via CDC Debezium).

Para iniciar tudo do zero, basta executar:

```bash
bash run.sh
```

O script fará o build das imagens, as carregará no cluster, fará o deploy e, ao final, iniciará automaticamente o **port-forward** da porta `3000`.

Quando a mensagem de "TUDO PRONTO!" aparecer, acesse no navegador: **http://localhost:3000**

> **Dica:** Para destruir o namespace e recriar o ambiente limpo do zero, utilize `bash run.sh --clean`

---

## Rodar o Projeto com Docker Compose (Alternativa)

Se você preferir não utilizar o Kubernetes, o Docker Compose possui todos os serviços mapeados para subir nativamente de uma só vez.

```bash
# Inicia todos os serviços em background e faz o build
docker compose up -d --build

# Para acompanhar os logs
docker compose logs -f

# Para parar a aplicação
docker compose down

# Para parar e apagar o banco de dados (reset completo)
docker compose down --volumes
```

Neste método, acesse: **http://localhost:3000**

---

## Executar Benchmark de Comparação (gRPC vs REST)

Foi implementado um ambiente para testes de carga utilizando **k6** para comparar a comunicação interna via gRPC contra REST HTTP/JSON.

**Nota de Arquitetura:** Para garantir uma comparação justa entre os protocolos sem sofrer com gargalos de threads ou do GIL do Python, o Serviço A (gRPC) utiliza **gRPC Assíncrono (`grpc.aio`)** junto com o driver de banco de dados não-bloqueante `asyncpg`, possuindo assim paridade arquitetural com o serviço REST (FastAPI).

Para rodar os testes:

1. Certifique-se de ter o cluster K8s/Kind rodando (execute `bash run.sh` previamente).
2. Certifique-se de ter o k6 instalado (veja os Pré-requisitos).
3. Execute o script unificado de benchmark, que gerencia automaticamente os port-forwards necessários e valida a saúde das rotas antes de inciar a carga:
   ```bash
   bash run-benchmark.sh
   ```

*(Desenvolvimento)*: Se você modificar o código-fonte de qualquer microsserviço, execute o comando com a flag de build para reconstruir as imagens Docker e recarregá-las no cluster local antes de testar:
```bash
bash run-benchmark.sh --build
```

Mais detalhes sobre a arquitetura do teste e analise de resultados podem ser encontrados em `benchmark/README.md`.

---

## Desenvolvimento Local (Rodar microsserviços individualmente)

Se você for modificar o código, precisará instalar as ferramentas das linguagens:

### Instalar mise (Gerenciador de Versões)

```bash
curl https://mise.run | sh
echo 'mise activate fish | source' >> ~/.config/fish/config.fish  # fish
# ou
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc                     # zsh
source ~/.config/fish/config.fish  # ou source ~/.zshrc
```

### Instalar Go via mise

```bash
mise use --global go@latest

# Dependencias proto/grpc
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# fish
fish_add_path ~/go/bin
# zsh
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### 1. Dependências Base (Postgres)
```bash
# Subir apenas o banco de dados
docker compose up postgres
```

### 2. Serviço A — Catálogo (Python gRPC)
```bash
cd microsservico-a
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Gera os stubs gRPC
python -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=. ../proto/biblioteca.proto

DATABASE_URL="postgresql://biblioteca:biblioteca@localhost:5432/biblioteca" GRPC_PORT=50051 python server.py
```

### 3. Serviço A-REST — Catálogo (Python FastAPI)
```bash
cd microsservico-a-rest
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

DATABASE_URL="postgresql://biblioteca:biblioteca@localhost:5432/biblioteca" REST_PORT=5001 uvicorn server:app --host 0.0.0.0 --port 5001
```

### 4. Serviço B — Busca (Java/Quarkus)
```bash
cd microsservico-b
DB_HOST=localhost ELASTICSEARCH_HOSTS=localhost:9200 ./mvnw compile quarkus:dev
```

### 5. Serviço P — API Gateway (Go)
```bash
cd microsservico-p
mkdir -p proto
protoc --go_out=./proto --go_opt=paths=source_relative --go-grpc_out=./proto --go-grpc_opt=paths=source_relative -I../proto ../proto/biblioteca.proto
go mod tidy

SERVICE_A_ADDR=localhost:50051 HTTP_PORT=8080 go run .
```

### 6. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

### Estrutura do projeto

```text
├── proto/
│   └── biblioteca.proto        # Contrato gRPC compartilhado
├── postgres/
│   └── init.sql                # Schemas catalogo + estoque
├── benchmark/
│   └── grpc_vs_rest.js         # Script k6 para teste de carga
├── microsservico-a/            # Python 3.12 — Catálogo (gRPC)
├── microsservico-a-rest/       # Python 3.12 — Catálogo (REST via FastAPI)
├── microsservico-b/            # Java/Quarkus — Busca (gRPC + REST JAX-RS)
├── microsservico-p/            # Go 1.22 — API Gateway
├── frontend/                   # React + Vite + Nginx
└── docker-compose.yml          # Definição dos containers
```