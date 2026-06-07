#!/bin/bash

if [ "$1" == "--clean" ]; then
    echo "Deletando namespace...."
    kubectl delete namespace "$NAMESPACE" --wait=true
fi

pkill -f "kubectl port-forward" 2>/dev/null

NAMESPACE="biblioteca"

if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    echo "O namespace '$NAMESPACE' já existe. Continuando...."
else
    echo "Namespace '$NAMESPACE' não encontrado. Criando...."
    kubectl create namespace "$NAMESPACE"
fi

kubectl apply -f k8s/

echo "Aguardando pods subirem..."

kubectl wait --for=condition=ready pod -l app=frontend -n biblioteca --timeout=90s

echo "Acesse em http://localhost:3000/ "

kubectl port-forward svc/frontend 3000:3000 -n biblioteca