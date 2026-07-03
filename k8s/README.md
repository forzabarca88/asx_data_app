# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the ASX Stock Analysis Dashboard.

## Files

- `Dockerfile` - Container definition for the Streamlit application
- `deployment.yaml` - Kubernetes Deployment with 2 replicas
- `service.yaml` - LoadBalancer Service to expose the application
- `ingress.yaml` - Ingress configuration for domain-based routing

## Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured
- Docker or container runtime for building images

## Deployment Steps

### 1. Build and push the Docker image

```bash
docker build -t asx-dashboard:latest .
docker tag asx-dashboard:latest your-registry/asx-dashboard:latest
docker push your-registry/asx-dashboard:latest
```

### 2. Apply Kubernetes manifests

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

### 3. Verify deployment

```bash
kubectl get pods
kubectl get services
kubectl get ingress
```

## Access the Application

Once deployed, access the dashboard via:
- LoadBalancer IP: `http://<EXTERNAL-IP>`
- Ingress domain: `http://asx-dashboard.example.com`

## Scaling

To scale the application:

```bash
kubectl scale deployment asx-dashboard --replicas=3
```

## Resource Management

The deployment includes resource requests and limits:
- **Requests**: 256Mi memory, 250m CPU
- **Limits**: 512Mi memory, 500m CPU

Adjust these values based on your cluster capacity and application needs.

## Notes

- The application uses Streamlit's built-in caching (`@st.cache_data`)
- Health checks are configured via HTTP probes
- CORS is disabled for security (set `STREAMLIT_SERVER_ENABLE_CORS=true` if needed)
