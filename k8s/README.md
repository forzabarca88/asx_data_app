# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the ASX Stock Analysis Dashboard.

## Files

- `Dockerfile` - Container definition for the Streamlit application
- `deployment.yaml` - Kubernetes Deployment with 1 replica
- `service.yaml` - NodePort Service to expose the application

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
- NodePort: `http://<NODE-IP>:30182`

## Scaling

To scale the application:

```bash
kubectl scale deployment asx-dashboard --replicas=3
```

Adjust these values based on your cluster capacity and application needs.

## Notes

- The application uses Streamlit's built-in caching (`@st.cache_data`)
- **Caching trade-off:** `@st.cache_data` is per-process. With 2 replicas, each pod
  independently fetches the bulk CSV / histories, doubling API load and giving
  inconsistent cache TTLs across pods. Consider running `replicas: 1` if API
  rate limits are a concern, or move caching to a shared layer (CDN, Redis).
- Health checks are configured via HTTP probes
- CORS is disabled for security (set `STREAMLIT_SERVER_ENABLE_CORS=true` if needed)
