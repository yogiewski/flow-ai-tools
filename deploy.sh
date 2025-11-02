#!/bin/bash

# Flow AI Chat Deployment Script

echo "🚀 Deploying Flow AI Chat..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ docker-compose is not available. Please install docker-compose."
    exit 1
fi

echo "✅ Docker found: $(docker --version)"
echo "✅ Compose found: $COMPOSE_CMD"

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local configuration file..."
    cat > .env.local << EOF
# Local environment overrides
# Configure your LLM settings here

LLM_BASE_URL=http://host.docker.internal
LLM_PORT=1234
LLM_API_FLAVOR=openai-compatible
LLM_DEFAULT_MODEL=gemma-2b
FLOWHUB_HOOKS_ENABLED=false
FLOWHUB_WEBHOOK_URL=
EOF
    echo "✅ Created .env.local - Edit it with your LLM configuration"
fi

# Create data directory if it doesn't exist
mkdir -p data/prompts

# Build and run the application
echo "🏗️ Building and starting the application..."
$COMPOSE_CMD up --build -d

# Wait for the container to start
echo "⏳ Waiting for the application to start..."
sleep 10

# Check if the container is running
if $COMPOSE_CMD ps | grep -q "llm-chat"; then
    echo "✅ Application deployed successfully!"
    echo ""
    echo "🌐 Access your app at: http://localhost:8501"
    echo ""
    echo "📝 To configure your LLM:"
    echo "   1. Edit .env.local with your LLM server details"
    echo "   2. Restart with: $COMPOSE_CMD restart"
    echo ""
    echo "📋 Useful commands:"
    echo "   • View logs: $COMPOSE_CMD logs -f"
    echo "   • Stop app: $COMPOSE_CMD down"
    echo "   • Restart: $COMPOSE_CMD restart"
else
    echo "❌ Failed to start the application. Check logs:"
    $COMPOSE_CMD logs
    exit 1
fi