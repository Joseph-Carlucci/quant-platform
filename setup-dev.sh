#!/bin/bash

# Quantitative Research Platform - Development Environment Setup
# This script prepares the local environment for new developers

echo "🚀 Setting up Quantitative Research Platform development environment..."

# Ensure required directories exist with proper permissions
echo "📁 Creating required directories..."
mkdir -p logs/scheduler
mkdir -p logs/dag_processor_manager  
mkdir -p plugins
chmod -R 755 logs plugins

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API keys and passwords!"
else
    echo "✅ .env file already exists"
fi

# Ensure Docker has the required permissions for volume mounts
echo "🐳 Setting up Docker permissions..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux: Set proper ownership for Airflow user (50000:0)
    sudo chown -R 50000:0 logs plugins
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Ensure directories are readable/writable
    chmod -R 777 logs plugins
fi

# Pull required Docker images
echo "📥 Pulling Docker images..."
docker-compose pull

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Edit .env file with your configuration"
echo "   2. Run: docker-compose up -d"
echo "   3. Wait ~2 minutes for services to start"
echo "   4. Access Airflow UI: http://localhost:8080 (admin/admin)"
echo "   5. Access pgAdmin: http://localhost:5050 (admin@example.com/admin)"
echo ""
echo "💡 Tip: Run 'docker-compose logs airflow' to monitor startup progress"