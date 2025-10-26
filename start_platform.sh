#!/bin/bash

echo "🚀 Starting Metropolis AI Platform"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start the platform
echo "🔨 Building and starting the platform..."
docker-compose up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Show logs for API service
echo "📝 API Service Logs:"
echo "==================="
docker-compose logs api --tail=20

echo ""
echo "🌐 Platform URLs:"
echo "================="
echo "API Documentation: http://localhost:8000/docs"
echo "Grafana Dashboard: http://localhost:3000"
echo "Prometheus: http://localhost:9090"
echo "Kibana: http://localhost:5601"
echo "MinIO Console: http://localhost:9001"

echo ""
echo "🧪 To test the API, run:"
echo "python test_api.py"

echo ""
echo "✅ Platform startup completed!"
