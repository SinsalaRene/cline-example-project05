#!/bin/bash

# Firewall Portal - Development Startup Script

set -e

echo "============================================"
echo "  Firewall Portal - Development Setup"
echo "============================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Build and start services
echo "Starting services..."
docker-compose up -d --build

echo ""
echo "============================================"
echo "  Services Started Successfully!"
echo "============================================"
echo ""
echo "  Frontend:  http://localhost:80"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  PgAdmin:   http://localhost:5050"
echo ""
echo "  Default login:"
echo "    Email: admin@example.com"
echo "    Pass:  (any)"
echo ""
echo "  Run 'docker-compose logs -f' to view logs"
echo "  Run 'docker-compose down' to stop services"
echo ""