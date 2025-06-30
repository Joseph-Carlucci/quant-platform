#!/bin/bash

# Troubleshoot Docker mount issues
echo "🔍 Diagnosing Docker mount issues..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Check current directory
echo "📁 Current directory: $(pwd)"

# Check if required files exist
echo "🔍 Checking required files..."
files=("docker-compose.yml" "init-db.sql" "dags" "logs" "plugins")
for file in "${files[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ $file exists"
        ls -la "$file"
    else
        echo "❌ $file missing"
    fi
done

# Check Docker file access permissions
echo "🔍 Checking Docker file access..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 macOS detected - checking Docker file access permissions"
    echo "   Go to: System Preferences > Security & Privacy > Privacy > Files and Folders"
    echo "   Ensure Docker has access to this directory: $(pwd)"
fi

# Test simple mount
echo "🧪 Testing simple Docker mount..."
if docker run --rm -v "$(pwd)":/test alpine ls /test >/dev/null 2>&1; then
    echo "✅ Basic Docker mounting works"
else
    echo "❌ Basic Docker mounting failed"
    echo "   This indicates a fundamental Docker mount permission issue"
fi

# Check for running containers that might conflict
echo "🔍 Checking for conflicting containers..."
conflicting=$(docker ps -a --filter name=quant- --format "table {{.Names}}\t{{.Status}}")
if [ -n "$conflicting" ]; then
    echo "⚠️  Found existing quant containers:"
    echo "$conflicting"
    echo "   Run: docker-compose down -v to clean up"
else
    echo "✅ No conflicting containers found"
fi

# Check available disk space
echo "🔍 Checking disk space..."
df -h .

echo ""
echo "🚨 If mounts still fail, try the alternative setup:"
echo "   docker-compose -f docker-compose.alternative.yml up -d"
echo ""
echo "🔧 Manual fix for mount permissions:"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "   sudo chown -R 50000:0 logs plugins dags"
    echo "   sudo chmod -R 755 logs plugins dags"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   chmod -R 777 logs plugins dags"
fi