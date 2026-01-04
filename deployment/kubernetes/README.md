# Kubernetes Deployment Guide

## Architecture

This deployment uses Kubernetes for orchestration, suitable for:
- AWS EKS
- Google GKE
- Azure AKS
- On-premises Kubernetes

## Components

- **Namespace**: `dhcs-bht`
- **Services**:
  - agent-api (Deployment + Service)
  - dashboard (Deployment + Service)
  - generator (Deployment)
  - kafka (StatefulSet via Strimzi operator)
  - pinot (StatefulSet)
  - chromadb (StatefulSet with PVC)

## Prerequisites

1. Kubernetes cluster (1.24+)
2. kubectl configured
3. Helm 3.x installed
4. OpenAI API key

## Quick Deploy

```bash
# 1. Create namespace
kubectl create namespace dhcs-bht

# 2. Create secret for OpenAI API key
kubectl create secret generic openai-api-key \
  --from-literal=OPENAI_API_KEY='your-key-here' \
  -n dhcs-bht

# 3. Install Strimzi Kafka operator
helm repo add strimzi https://strimzi.io/charts/
helm install kafka-operator strimzi/strimzi-kafka-operator \
  --namespace dhcs-bht

# 4. Deploy Kafka cluster
kubectl apply -f deployment/kubernetes/kafka-cluster.yaml

# 5. Deploy Pinot
kubectl apply -f deployment/kubernetes/pinot.yaml

# 6. Deploy AI services
kubectl apply -f deployment/kubernetes/agent-api.yaml
kubectl apply -f deployment/kubernetes/dashboard.yaml
kubectl apply -f deployment/kubernetes/generator.yaml

# 7. Expose dashboard
kubectl port-forward svc/dashboard 8501:8501 -n dhcs-bht
```

## Production Considerations

### High Availability
- Run 3+ Kafka brokers
- Run 2+ agent-api replicas
- Use pod anti-affinity rules

### Autoscaling
```bash
kubectl apply -f deployment/kubernetes/hpa.yaml
```

### Monitoring
- Prometheus for metrics
- Grafana for dashboards
- Jaeger for tracing

### Storage
- Use StorageClass with dynamic provisioning
- EBS/EFS on AWS
- Persistent Disk on GCP
- Azure Disk on Azure

## Resource Requirements

### Minimum (Development)
- 4 vCPUs
- 8 GB RAM
- 20 GB storage

### Recommended (Production)
- 16+ vCPUs
- 32+ GB RAM
- 100+ GB storage with fast SSD
