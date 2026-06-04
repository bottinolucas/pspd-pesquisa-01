# Biblioteca Distribuída

Aplicação distribuída com arquitetura gRPC — trabalho prático de Programacao para Sistemas Paralelos e Distribuídos (UnB).

## Arquitetura

```
[Browser] ──HTTP──► [Frontend React :3000]
                            │
                       /api/* (Nginx proxy)
                            │
                    [P: Go/Gin :8080]  ← API Gateway + gRPC Stub 
                     │            │
               gRPC :50051   gRPC :50052
                     │            │
            [A: Python]          [B: Java]
            Catálogo             Estoque / Empréstimos
            schema: catalogo     schema: estoque 
                     |            |  
                     │            │  
                     └─────┬──────┘
                           │
                   [PostgreSQL :5432]
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

### 3. Serviço P — API Gateway (Go)

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

### 4. Frontend (React + Vite)

```bash
cd frontend

npm install

npm run dev
```

Acessa em: **http://localhost:3000**

> O Vite já faz proxy de `/api/*` para `localhost:8080` automaticamente (configurado no `vite.config.js`).

### Ordem de inicialização

```
postgres → microsservico-a → microsservico-p → frontend
```

## Estrutura do projeto

```
.
├── proto/
│   └── biblioteca.proto        # Contrato gRPC compartilhado
├── postgres/
│   └── init.sql                # Schemas catalogo + estoque
├── microsservico-a/            # Python 3.12 — Catálogo
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── microsservico-p/            # Go 1.22 — API Gateway
│   ├── main.go
│   ├── handlers.go
│   ├── context.go
│   ├── go.mod
│   └── Dockerfile
├── frontend/                   # React + Vite + Nginx
│   ├── src/
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml
```