#!/bin/bash

# Development Environment Setup
echo "🚀 Setting up development environment..."

# Create required directories
mkdir -p logs/scheduler logs/dag_processor_manager plugins

# Set proper permissions for Airflow (runs as UID 50000)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo chown -R 50000:0 logs plugins
else
    chmod -R 777 logs plugins  
fi

# Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    cp env.example .env
    echo "📝 Created .env file - please edit with your API keys"
fi

# Ensure init-db.sql is readable
chmod 644 init-db.sql

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"  
echo "2. Run: docker-compose up -d"
echo "3. Access Airflow: http://localhost:8080 (admin/admin)"
echo "4. Access pgAdmin: http://localhost:5050 (admin@example.com/admin)"