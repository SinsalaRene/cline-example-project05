# Deployment Runbook

## Pre-Deployment Checklist

- [ ] All CI checks pass
- [ ] Database migration tested in staging
- [ ] Rollback plan documented
- [ ] Stakeholders notified

## Deployment Steps

### 1. Backend Deployment

```bash
# Build and push images
docker build -t registry/backend:<tag> -f backend/Dockerfile backend/
docker push registry/backend:<tag>

# Deploy to AKS
kubectl set image deployment/backend backend=registry/backend:<tag>
kubectl rollout status deployment/backend
kubectl rollout history deployment/backend
```

### 2. Frontend Deployment

```bash
# Build and push frontend image
docker build -t registry/frontend:<tag> -f frontend/Dockerfile frontend/
docker push registry/frontend:<tag>

# Deploy
kubectl set image deployment/frontend frontend=registry/frontend:<tag>
kubectl rollout status deployment/frontend
```

## Post-Deployment Verification

```bash
# Check health endpoints
curl -f https://api.example.com/health
curl -f https://api.example.com/api/v1/stats/health

# Run smoke tests
pytest tests/smoke/ -v
```

## Rollback Procedure

```bash
# Get previous image tag
kubectl rollout history deployment/backend
kubectl rollout undo deployment/backend
kubectl rollout undo deployment/frontend
```

## Incident Response

### High Error Rate

1. Check logs: `kubectl logs -l app=backend --tail=100`
2. Check metrics: Grafana dashboard
3. If DB issue: Check connection pool usage
4. Consider rollback if error rate > 5%

### Database Connection Issues

1. Check PostgreSQL pod status: `kubectl get pods -l app=postgresql`
2. Check connection pool: `kubectl exec -it <pod> -- psql -c "SELECT count(*) FROM pg_stat_activity;"`
3. Scale down backend if needed: `kubectl scale deployment/backend --replicas=0`
4. Restart PostgreSQL pod: `kubectl delete pod <postgresql-pod>`

### Memory/CPU Issues

1. Check resource usage: `kubectl top pods`
2. Scale up deployment: `kubectl scale deployment/backend --replicas=3`
3. If persistent, review memory leaks and optimize

### Cache Failures

1. Check Redis health: `kubectl exec -it <redis-pod> -- redis-cli ping`
2. Restart Redis if needed: `kubectl rollout restart deployment/redis`
3. Verify backend can reconnect