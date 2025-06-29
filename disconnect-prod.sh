#!/bin/bash

# Stop Production Port-Forwards

echo "🛑 Disconnecting from production services..."

# Kill port-forwards
lsof -ti:8081 | xargs kill -9 2>/dev/null || true
lsof -ti:15432 | xargs kill -9 2>/dev/null || true

# Clean up log files
rm -f /tmp/airflow-port-forward.log /tmp/postgres-port-forward.log

echo "✅ Production port-forwards stopped"