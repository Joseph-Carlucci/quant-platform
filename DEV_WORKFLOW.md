# Development Workflow Guide

## Overview

This guide explains the simple development workflow for your quantitative research platform using Docker and production connection scripts.

## 🚀 Local Development Setup

### Start Local Environment
```bash
# Start all local services
docker compose up -d

# Check status
docker compose ps
```

**What this provides:**
- ✅ Local Airflow for DAG development
- ✅ Local pgAdmin for database queries
- ✅ Local PostgreSQL with your data
- ✅ Fast development feedback loop

### Stop Local Environment
```bash
docker compose down
```

## ☁️ Production Access

### Connect to Production
```bash
# Connect to production services
./connect-prod.sh
```

**What this does:**
- ✅ Sets up port-forwarding to production Airflow (8081)
- ✅ Sets up port-forwarding to production pgAdmin (5051)  
- ✅ Runs in background, returns your terminal
- ✅ Provides secure access to live production data

### Disconnect from Production
```bash
./disconnect-prod.sh
```

## 🎯 Access Points

### Local Development
- **Airflow:** http://localhost:8080
- **pgAdmin:** http://localhost:5050
- **PostgreSQL:** localhost:5432
- **Credentials:** From your `.env` file

### Production Access
- **Airflow:** http://localhost:8081
- **pgAdmin:** http://localhost:5051
- **PostgreSQL:** Internal to cluster only
- **Credentials:** From your GitHub repository secrets

## 🔄 Typical Development Workflow

### 1. Start Local Development
```bash
# Start local environment
docker compose up -d
```

### 2. Develop and Test Locally
- Edit DAGs in `dags/` directory
- Test with local Airflow (http://localhost:8080)
- Query data with local pgAdmin (http://localhost:5050)
- Iterate quickly with local environment

### 3. Deploy to Production
```bash
# Commit your changes
git add .
git commit -m "Your changes"
git push origin main
```
This triggers CI/CD deployment to production.

### 4. Verify in Production
```bash
# Connect to production
./connect-prod.sh

# Check production Airflow (http://localhost:8081)
# Verify data in production pgAdmin (http://localhost:5051)

# When done
./disconnect-prod.sh
```

### 5. End Development Session
```bash
# Stop local Docker
docker compose down
```

## 🔧 Production Connection Features

### Simple Port-Forwarding
- **`./connect-prod.sh`:** Sets up background port-forwards to production
- **`./disconnect-prod.sh`:** Cleanly stops all production connections
- **No terminal blocking:** Port-forwards run in background
- **Automatic cleanup:** Handles existing connections gracefully

### Port Separation
- **Local services:** Standard ports (8080, 5050, 5432)
- **Production access:** Offset ports (8081, 5051)
- **No conflicts:** Can run both environments simultaneously

### Logging
- **Connection logs:** Saved to `/tmp/*-port-forward.log`
- **Error debugging:** Check logs if connections fail
- **Clean shutdown:** Logs cleaned up on disconnect

## 🛠️ Manual Alternatives

### Manual Docker Commands
```bash
# Start local development
docker compose up -d

# Check container status
docker compose ps

# View logs
docker compose logs

# Stop local development
docker compose down
```

### Manual Production Port-Forwarding
```bash
# Terminal 1: Airflow
kubectl port-forward -n quant-platform service/airflow 8081:8080

# Terminal 2: pgAdmin
kubectl port-forward -n quant-platform service/pgladmin 5051:5050
```

### Check What's Running
```bash
# Local Docker containers
docker compose ps

# Production port-forwards
ps aux | grep "kubectl port-forward"

# Check connection logs
tail -f /tmp/airflow-port-forward.log
tail -f /tmp/pgladmin-port-forward.log
```

## 🐛 Troubleshooting

### Script Won't Start
```bash
# Check requirements
docker --version
kubectl version --client
docker-compose --version

# Check Docker daemon
docker ps

# Check cluster connection
kubectl get pods -n quant-platform
```

### Port Conflicts
```bash
# See what's using a port
lsof -i :8080
lsof -i :8081

# Kill process on port
lsof -ti:8080 | xargs kill -9
```

### Production Services Not Ready
```bash
# Check pod status
kubectl get pods -n quant-platform

# Check specific service
kubectl describe pod -l app=airflow -n quant-platform

# Check recent deployments
kubectl get events -n quant-platform --sort-by='.lastTimestamp'
```

### Clean Reset
```bash
# Stop everything
./stop-dev.sh
docker-compose down

# Clean port-forward PIDs
rm -f /tmp/quant-*-port-forward.pid

# Start fresh
./start-dev.sh
```

## 📁 File Structure

```
quant-platform/
├── start-dev.sh          # Start development environment
├── stop-dev.sh           # Stop production port-forwards
├── docker-compose.yml    # Local development services
├── .env                  # Local environment variables
├── dags/                 # Airflow DAGs
└── k8s/                  # Kubernetes configurations
```

## 🎯 Best Practices

### Environment Variables
- **Local:** Use `.env` file for development credentials
- **Production:** Use GitHub repository secrets for CI/CD
- **Never commit** real credentials to version control

### Development Cycle
1. **Develop locally** with fast feedback loop
2. **Test locally** with your own data/credentials  
3. **Deploy to production** via git push (triggers CI/CD)
4. **Verify in production** via port-forwarding

### Security
- **Local:** Open ports for convenience (development only)
- **Production:** ClusterIP services + port-forwarding only
- **Credentials:** Separate for each environment

---

**🚀 Ready to start developing? Run `./start-dev.sh` and you're good to go!**