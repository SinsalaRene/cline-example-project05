# Backup & Restore Procedures

## Automated Backups

PostgreSQL is configured with automated backups (35-day retention).

### Backup Schedule

| Type | Frequency | Retention |
|------|-----------|-----------|
| Continuous WAL | Every 5 min | 7 days |
| Daily full | Daily 02:00 UTC | 35 days |

## Manual Backup

### Backup Database

```bash
# Set variables
DB_HOST=<postgresql-server>
DB_USER=postgres
DB_NAME=fw_portal
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).backup"

# Create backup
pg_dump -h "$DB_HOST" -U "$DB_USER" -F c -f "$BACKUP_FILE" "$DB_NAME"
```

### Backup Configuration

```bash
# Export ConfigMap
kubectl get configmap backend-config -o yaml > backup-config.yaml

# Export Secrets (base64 encoded)
kubectl get secret backend-secret -o json | jq '.data' > backup-secret-data.json
```

## Restore Procedures

### Restore Database from Backup

```bash
# Variables
DB_HOST=<postgresql-server>
DB_USER=postgres
DB_NAME=fw_portal

# Stop application to prevent writes
kubectl scale deployment/backend --replicas=0

# Drop and recreate database (optional - for clean restore)
psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -h "$DB_HOST" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

# Restore from backup
pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" "$BACKUP_FILE"

# Verify restore
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) FROM firewall_rules;"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) FROM audit_log;"

# Restart application
kubectl scale deployment/backend --replicas=2

# Verify health
curl -f https://api.example.com/health
```

### Restore Configuration

```bash
# Apply backup ConfigMap
kubectl apply -f backup-config.yaml

# Apply backup Secret data
kubectl apply -f backup-secret-data.json
```

### Full Restore (Disaster Recovery)

```bash
# 1. Provision new infrastructure (Terraform)
cd infrastructure/terraform
terraform init
terraform apply

# 2. Restore database
pg_restore -h "$NEW_DB_HOST" -U postgres -d fw_portal "$BACKUP_FILE"

# 3. Deploy applications
kubectl apply -f ../kubernetes/
kubectl set env deployment/backend DB_HOST="$NEW_DB_HOST"

# 4. Update DNS
# Point domain to new LoadBalancer IP
```

## Testing Restores

### Restore Test Schedule

| Test | Frequency | Data Used |
|------|-----------|-----------|
| Unit test | Every deploy | In-memory |
| Integration test | Weekly | Staging clone |
| Full DR drill | Quarterly | Production copy |

### Restore Test Script

```bash
# Run restore test
docker compose -f docker-compose.test.yml up -d

# Restore latest backup into test database
bash scripts/restore_test.sh

# Run verification
pytest tests/test_restore.py -v

# Cleanup
docker compose -f docker-compose.test.yml down
```

## Monitoring

### Backup Health

```bash
# Check backup status (if using cloud provider)
az postgres flexible-server backup list \
  --resource-group <rg> \
  --name <server>

# Check backup age
kubectl get jobs -l type=backup -o jsonpath='{.items[0].status.completionTime}'
```

### Alert Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| Backup failed | Critical | Immediate retry + notify |
| Backup > 25h old | Warning | Check schedule |
| Storage > 80% | Warning | Clean old backups |
| Restore failed | Critical | Investigate + retry |