# Production Access Guide

## Overview

This guide explains how to securely access your production quantitative research platform deployed on Kubernetes.

## 🚀 Quick Start

### Use the Connection Script (Recommended)
```bash
./scripts/connect.sh
```

This interactive script will:
- Check service status
- Set up port-forwarding on non-conflicting ports
- Provide connection instructions
- Manage multiple connections

### Manual Port-Forwarding
```bash
# Production Airflow (port 8081 to avoid local conflict)
kubectl port-forward -n quant-platform service/airflow 8081:8080

# Production pgAdmin (port 5051 to avoid local conflict)
kubectl port-forward -n quant-platform service/pgadmin 5051:80
```

## 🔐 Service Access

### Production Airflow
- **URL:** http://localhost:8081
- **Username:** Your `AIRFLOW_ADMIN_USERNAME` GitHub secret
- **Password:** Your `AIRFLOW_ADMIN_PASSWORD` GitHub secret

### Production pgAdmin
- **URL:** http://localhost:5051
- **Email:** Your `PGADMIN_EMAIL` GitHub secret
- **Password:** Your `PGADMIN_PASSWORD` GitHub secret

## 🐘 Setting Up PostgreSQL Connection in pgAdmin

Once logged into **production pgAdmin** (http://localhost:5051):

### Step 1: Add Server
1. Right-click **"Servers"** in the left panel
2. Select **"Register"** → **"Server"**

### Step 2: General Settings
- **Name:** `Production Quant Database`
- **Server Group:** `Servers` (default)
- **Comments:** `Production PostgreSQL for Quant Platform`

### Step 3: Connection Settings
- **Host name/address:** `postgres`
- **Port:** `5432`
- **Maintenance database:** `postgres`
- **Username:** `postgres`
- **Password:** Your `POSTGRES_PASSWORD` GitHub secret value

### Step 4: Advanced Settings (Optional)
- **Connection timeout:** `10`
- **Auto-reconnect:** `Yes`

### Step 5: Save
Click **"Save"** to create the connection.

## 🔄 Simultaneous Dev/Prod Access

You can access both environments simultaneously:

### Local Development
- **Airflow:** http://localhost:8080
- **pgAdmin:** http://localhost:5050
- **Credentials:** From your `.env` file

### Production
- **Airflow:** http://localhost:8081 (via port-forward)
- **pgAdmin:** http://localhost:5051 (via port-forward)
- **Credentials:** From GitHub secrets

## 📊 Database Schema Access

### Production Databases
Once connected to production PostgreSQL, you'll see:
- `postgres` - Default database
- `airflow` - Airflow metadata
- `quant_data` - Your quantitative data (if created)

### Key Tables
```sql
-- View trading signals
SELECT * FROM signals ORDER BY created_at DESC LIMIT 10;

-- Check model performance
SELECT * FROM model_performance ORDER BY sharpe_ratio DESC;

-- See market data
SELECT * FROM market_data ORDER BY date DESC LIMIT 20;
```

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Kill process using port 8081
lsof -ti:8081 | xargs kill -9

# Kill process using port 5051
lsof -ti:5051 | xargs kill -9
```

### Can't Connect to Cluster
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name quant-platform

# Verify connection
kubectl get pods -n quant-platform
```

### Service Not Ready
```bash
# Check pod status
kubectl get pods -n quant-platform

# Check specific service logs
kubectl logs -f deployment/airflow -n quant-platform
kubectl logs -f deployment/pgadmin -n quant-platform
kubectl logs -f deployment/postgres -n quant-platform
```

### pgAdmin Won't Connect to PostgreSQL
1. **Check PostgreSQL pod is running:**
   ```bash
   kubectl get pods -n quant-platform -l app=postgres
   ```

2. **Verify PostgreSQL service:**
   ```bash
   kubectl get svc postgres -n quant-platform
   ```

3. **Test connection from pgAdmin pod:**
   ```bash
   kubectl exec -it deployment/pgadmin -n quant-platform -- ping postgres
   ```

4. **Check secret values:**
   ```bash
   kubectl get secret quant-secrets -n quant-platform -o yaml
   ```

## 🔧 Useful Commands

### Service Management
```bash
# Restart a service
kubectl rollout restart deployment/airflow -n quant-platform

# Scale a service
kubectl scale deployment airflow --replicas=2 -n quant-platform

# Check resource usage
kubectl top pods -n quant-platform
```

### Logs and Debugging
```bash
# Follow logs
kubectl logs -f deployment/airflow -n quant-platform

# Get all events
kubectl get events -n quant-platform --sort-by='.lastTimestamp'

# Describe a pod
kubectl describe pod <pod-name> -n quant-platform
```

### Secret Management
```bash
# List secrets
kubectl get secrets -n quant-platform

# Decode a secret (base64)
kubectl get secret quant-secrets -n quant-platform -o jsonpath='{.data.postgres-password}' | base64 -d
```

## 🚨 Security Best Practices

### 1. Always Use Port-Forwarding
- Never expose services directly via LoadBalancer in production
- Use ClusterIP services with kubectl port-forward
- Limit port-forward to localhost only

### 2. Rotate Credentials Regularly
```bash
# Update GitHub secrets periodically
gh secret set POSTGRES_PASSWORD
gh secret set PGADMIN_PASSWORD
gh secret set AIRFLOW_ADMIN_PASSWORD
```

### 3. Monitor Access
```bash
# Check who's accessing your cluster
kubectl get events -n quant-platform --field-selector reason=PortForward

# Monitor resource usage
kubectl top pods -n quant-platform
```

### 4. Use Strong Passwords
- Minimum 12 characters
- Mix of letters, numbers, symbols
- Unique for each service
- Never share or commit to version control

## 📚 Quick Reference

### Connection Ports
| Service | Local Dev | Production |
|---------|-----------|------------|
| Airflow | 8080 | 8081 |
| pgAdmin | 5050 | 5051 |
| PostgreSQL | 5432 | (internal only) |

### Access Commands
```bash
# Connect to production
./scripts/connect.sh

# Manual port-forward (production)
kubectl port-forward -n quant-platform service/airflow 8081:8080
kubectl port-forward -n quant-platform service/pgadmin 5051:80

# Check status
kubectl get all -n quant-platform
```

---

**🎯 You're now ready to securely access your production quantitative research platform!**