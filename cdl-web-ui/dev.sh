#!/bin/bash

# CDL Web UI Development Helper Script

set -e

COMMAND=${1:-""}

show_help() {
    echo "CDL Web UI Development Helper"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev     Start development environment with hot reloading"
    echo "  build   Build production version"
    echo "  stop    Stop all containers"
    echo "  logs    Show application logs"
    echo "  clean   Clean up containers and volumes"
    echo "  shell   Open shell in running container"
    echo "  help    Show this help message"
    echo ""
    echo "For development, just run:"
    echo "  $0 dev"
}

case $COMMAND in
    "dev")
        echo "🚀 Starting CDL Web UI in development mode..."
        echo "📁 Hot reloading enabled - code changes will be reflected automatically"
        echo "🌐 Application will be available at: http://localhost:3001"
        echo ""
        docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
        ;;
    "build")
        echo "🔨 Building production version..."
        docker-compose -f docker-compose.yml build
        ;;
    "stop")
        echo "🛑 Stopping CDL Web UI..."
        docker-compose -f docker-compose.yml -f docker-compose.override.yml down
        ;;
    "logs")
        echo "📋 Showing application logs..."
        docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f cdl-web-ui
        ;;
    "clean")
        echo "🧹 Cleaning up containers and volumes..."
        docker-compose -f docker-compose.yml -f docker-compose.override.yml down -v --remove-orphans
        docker system prune -f
        ;;
    "shell")
        echo "🐚 Opening shell in container..."
        docker-compose -f docker-compose.yml -f docker-compose.override.yml exec cdl-web-ui sh
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac