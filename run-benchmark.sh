#!/bin/bash
# Script para rodar o benchmark gRPC vs REST
# Uso: ./run-benchmark.sh [--build]
#   --build  Reconstrói as imagens Docker e recarrega no Kind (usar quando alterar código)
# Pré-requisito: cluster K8s rodando (execute run.sh antes)

set -e

NAMESPACE="biblioteca"
KIND_CLUSTER="kind"
GATEWAY_URL="http://localhost:8080"

echo "╔══════════════════════════════════════════════════╗"
echo "║  Benchmark: gRPC vs REST                         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Verifica se o k6 está instalado
if ! command -v k6 &> /dev/null; then
    echo "ERRO: k6 não está instalado."
    echo "Instale: https://k6.io/docs/get-started/installation/"
    exit 1
fi

# ── Build (somente com --build) ───────────────────────────────────────────────
if [ "$1" == "--build" ]; then
    echo "Construindo imagens Docker..."
    docker build -t thegm445/biblioteca-catalogo:latest      -f microsservico-a/Dockerfile      . 
    docker build -t thegm445/biblioteca-rest-catalogo:latest  -f microsservico-a-rest/Dockerfile  .
    docker build -t thegm445/biblioteca-busca:latest          -f microsservico-b/Dockerfile       .
    docker build -t thegm445/biblioteca-gateway:latest        -f microsservico-p/Dockerfile       .

    echo ""
    echo "Carregando imagens no cluster Kind..."
    kind load docker-image thegm445/biblioteca-catalogo:latest      --name "$KIND_CLUSTER"
    kind load docker-image thegm445/biblioteca-rest-catalogo:latest --name "$KIND_CLUSTER"
    kind load docker-image thegm445/biblioteca-busca:latest         --name "$KIND_CLUSTER"
    kind load docker-image thegm445/biblioteca-gateway:latest       --name "$KIND_CLUSTER"

    echo ""
    echo "Reiniciando deployments para usar as imagens atualizadas..."
    kubectl rollout restart deployment/microsservico-a      -n "$NAMESPACE"
    kubectl rollout restart deployment/microsservico-a-rest -n "$NAMESPACE"
    kubectl rollout restart deployment/microsservico-b      -n "$NAMESPACE"
    kubectl rollout restart deployment/microsservico-p      -n "$NAMESPACE"

    echo "Aguardando gateway ficar pronto..."
    kubectl rollout status deployment/microsservico-p -n "$NAMESPACE" --timeout=120s
fi

# ── Port-forward do Gateway ──────────────────────────────────────────────────
pkill -f "kubectl port-forward.*microsservico-p" 2>/dev/null || true
sleep 1

echo "Aguardando gateway ficar pronto..."
kubectl wait --for=condition=ready pod -l app=microsservico-p -n "$NAMESPACE" --timeout=120s

kubectl port-forward svc/microsservico-p 8080:8080 -n "$NAMESPACE" &
PF_PID=$!
sleep 3

# ── Verificação de conectividade ─────────────────────────────────────────────
echo ""
echo "Testando rotas..."
GRPC_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/api/v1/livros")
REST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/api/v2/livros")
echo "  /api/v1/livros (gRPC) → HTTP $GRPC_RESPONSE"
echo "  /api/v2/livros (REST) → HTTP $REST_RESPONSE"

if [ "$GRPC_RESPONSE" != "200" ] || [ "$REST_RESPONSE" != "200" ]; then
    echo ""
    echo "ATENÇÃO: Uma ou mais rotas não retornaram 200."
    echo "   Verifique os logs: kubectl logs deployment/microsservico-p -n $NAMESPACE"
    kill $PF_PID 2>/dev/null
    exit 1
fi

# ── Executar k6 ──────────────────────────────────────────────────────────────
echo ""
echo "Iniciando benchmark k6..."
echo "──────────────────────────────────────────────────"
k6 run --env GATEWAY_URL="$GATEWAY_URL" benchmark/grpc_vs_rest.js

# Limpa port-forward
kill $PF_PID 2>/dev/null
