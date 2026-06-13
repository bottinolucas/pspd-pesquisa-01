#!/bin/bash

NAMESPACE="biblioteca"

pkill -f "kubectl port-forward" 2>/dev/null

if [ "$1" == "--clean" ]; then
    echo "Limpando tudo..."
    kubectl delete namespace "$NAMESPACE" --wait=true 2>/dev/null
fi

if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    echo "Criando namespace '$NAMESPACE'..."
    kubectl create namespace "$NAMESPACE"
fi

echo "Sincronizando ConfigMap..."
kubectl create configmap postgres-init \
  --from-file=postgres/init.sql \
  -n "$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f - -n "$NAMESPACE"

echo "Aplicando..."
kubectl apply -f k8s/ -n "$NAMESPACE"

# Eu nao recomendo....MAS
# Se voce quer resetar o banco toda vez, descomente a linha abaixo
# kubectl delete pod -l app=postgres -n "$NAMESPACE"

echo "Aguardando pods ficarem prontos...(pode ser que demore alguns minutos na primeira vez)"
kubectl wait --for=condition=ready pod -l app=frontend -n "$NAMESPACE" --timeout=90s
kubectl wait --for=condition=ready pod -l app=microsservico-b -n "$NAMESPACE" --timeout=90s

# Força o CDC (Debezium) a sincronizar os dados do init.sql para o Elasticsearch.
# O Debezium só captura mudanças; dados inseridos antes dele conectar ficam invisíveis.
echo "Sincronizando dados para Elasticsearch (CDC)..."
sleep 5
kubectl exec deployment/postgres -n "$NAMESPACE" -- \
  psql -U biblioteca -d biblioteca -c "UPDATE catalogo.livros SET titulo = titulo;" 2>/dev/null

echo "----------------------------------------------------"
echo "TUDO PRONTO! Acesse: http://localhost:3000"
echo "----------------------------------------------------"

kubectl port-forward svc/frontend 3000:3000 -n "$NAMESPACE"