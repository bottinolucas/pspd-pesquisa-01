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

## Pré-requisitos

- Docker + Docker Compose
- mise (gerenciador de versões)
- Go (via mise)
- protoc

### Instalar mise

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

### Permissão Docker

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## Rodar com Docker Compose (recomendado)

```bash
# Primeira vez (ou após mudanças no código)
docker compose up --build

# Próximas vezes
docker compose up

# Parar
docker compose down

# Parar e apagar o banco de dados
docker compose down --volumes
```

Acessa em: **http://localhost:3000**

---

## Rodar com Kubernetes (minikube/kind)

Se você preferir rodar a arquitetura dentro de um cluster Kubernetes local (ex: Minikube ou Kind), a infraestrutura também está configurada na pasta `k8s/`.

Existe um script facilitador que configura os ConfigMaps e aplica os arquivos YAML:

```bash
# Executar script que cria o namespace 'biblioteca' e faz o apply dos manifests
bash run.sh
```
O script fará o **port-forward** automático da porta `3000` do frontend no final da execução. Para testar do zero e recriar o cluster (exclui o namespace), utilize:
```bash
bash run.sh --clean
```

---

## Executar Benchmark de Comparação (gRPC vs REST)

Foi implementado um ambiente para testes de carga utilizando **k6** para comparar a comunicação interna via gRPC contra REST HTTP/JSON.
Para rodar os testes:

1. Suba os containers com `docker compose up -d`
2. Certifique-se de ter o [k6 instalado](https://k6.io/docs/get-started/installation/)
3. Execute o script de benchmark:
   ```bash
   k6 run benchmark/grpc_vs_rest.js
   ```

Mais detalhes e execução via Kubernetes podem ser encontrados em `benchmark/README.md`.

---

## Rodar cada serviço individualmente (dev)

### 1. Postgres (sempre necessário)

```bash
docker compose up postgres
```

### 2. Serviço A — Catálogo (Python)

```bash
cd microsservico-a

# Criando ambiente virtual e instalando dependencias
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Gera os stubs gRPC
python -m grpc_tools.protoc \
  -I../proto \
  --python_out=. \
  --grpc_python_out=. \
  ../proto/biblioteca.proto

# Roda
DATABASE_URL="postgresql://biblioteca:biblioteca@localhost:5432/biblioteca" \
GRPC_PORT=50051 \
python server.py
```

```

### 3. Serviço A-REST — Catálogo (REST via FastAPI)

```bash
cd microsservico-a-rest

# Criando ambiente virtual e instalando dependencias
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Roda
DATABASE_URL="postgresql://biblioteca:biblioteca@localhost:5432/biblioteca" \
REST_PORT=5001 \
uvicorn server:app --host 0.0.0.0 --port 5001
```

### 4. Serviço B — Busca (Java/Quarkus)

```bash
cd microsservico-b

# Roda em dev mode (necessário Java 21+ e Maven)
DB_HOST=localhost \
ELASTICSEARCH_HOSTS=localhost:9200 \
./mvnw compile quarkus:dev
```

### 5. Serviço P — API Gateway (Go)

```bash
cd microsservico-p

# Gera os stubs gRPC (só na primeira vez)
mkdir -p proto
protoc \
  --go_out=./proto --go_opt=paths=source_relative \
  --go-grpc_out=./proto --go-grpc_opt=paths=source_relative \
  -I../proto \
  ../proto/biblioteca.proto

go mod tidy

# Roda
SERVICE_A_ADDR=localhost:50051 HTTP_PORT=8080 go run .
```

### 6. Frontend (React + Vite)

```bash
cd frontend

npm install

npm run dev
```

Acessa em: **http://localhost:3000**

> O Vite já faz proxy de `/api/*` para `localhost:8080` automaticamente (configurado no `vite.config.js`).

### Ordem de inicialização

```
postgres → microsservico-a (e/ou a-rest) → microsservico-b → microsservico-p → frontend
```

## Estrutura do projeto

├── proto/
│   └── biblioteca.proto        # Contrato gRPC compartilhado
├── postgres/
│   └── init.sql                # Schemas catalogo + estoque
├── benchmark/
│   └── grpc_vs_rest.js         # Script k6 para teste de carga
├── microsservico-a/            # Python 3.12 — Catálogo (gRPC)
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── microsservico-a-rest/       # Python 3.12 — Catálogo (REST via FastAPI)
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── microsservico-b/            # Java/Quarkus — Busca (gRPC + REST JAX-RS)
│   ├── src/
│   ├── pom.xml
│   └── Dockerfile
├── microsservico-p/            # Go 1.22 — API Gateway
│   ├── main.go
│   ├── handlers.go
│   ├── rest_handlers.go
│   ├── rest_client.go
│   ├── go.mod
│   └── Dockerfile
├── frontend/                   # React + Vite + Nginx
│   ├── src/
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml
```