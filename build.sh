#!/bin/bash
# WhisperEngine Build Script
# Convenient wrapper for cross-platform builds

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[BUILD]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
check_venv() {
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        print_warning "No virtual environment detected"
        if [[ -d ".venv" ]]; then
            print_status "Activating .venv..."
            source .venv/bin/activate
        else
            print_error "No .venv directory found. Please create virtual environment first."
            exit 1
        fi
    else
        print_status "Using virtual environment: $VIRTUAL_ENV"
    fi
}

# Install build dependencies
install_deps() {
    print_status "Checking build dependencies..."
    
    # Check if PyInstaller is installed
    if ! python -c "import PyInstaller" 2>/dev/null; then
        print_status "Installing PyInstaller..."
        pip install PyInstaller
    fi
    
    print_success "Build dependencies ready"
}

# Show help
show_help() {
    echo "WhisperEngine Build Script"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  build          Build for current platform"
    echo "  build-all      Build for all supported platforms"
    echo "  clean          Clean build artifacts"
    echo "  test           Test the built application"
    echo "  info           Show build environment info"
    echo "  help           Show this help message"
    echo
    echo "Options:"
    echo "  --no-clean     Skip cleaning before build"
    echo "  --platform     Target platform (darwin, windows, linux)"
    echo
    echo "Examples:"
    echo "  $0 build                    # Build for current platform"
    echo "  $0 build --platform darwin # Build for macOS"
    echo "  $0 build-all               # Build for all platforms"
    echo "  $0 clean                   # Clean build artifacts"
    echo "  $0 test                    # Test built application"
}

# Test the built application
test_app() {
    print_status "Testing built application..."
    
    # Determine the executable based on platform
    case "$(uname -s)" in
        Darwin)
            APP_PATH="dist/WhisperEngine.app"
            if [[ -d "$APP_PATH" ]]; then
                print_status "Testing macOS app bundle..."
                open "$APP_PATH" &
                sleep 3
                print_success "macOS app launched successfully"
            else
                print_error "macOS app bundle not found: $APP_PATH"
                exit 1
            fi
            ;;
        Linux)
            APP_PATH="dist/WhisperEngine"
            if [[ -f "$APP_PATH" ]]; then
                print_status "Testing Linux executable..."
                "$APP_PATH" &
                sleep 3
                print_success "Linux executable launched successfully"
            else
                print_error "Linux executable not found: $APP_PATH"
                exit 1
            fi
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            APP_PATH="dist/WhisperEngine.exe"
            if [[ -f "$APP_PATH" ]]; then
                print_status "Testing Windows executable..."
                "$APP_PATH" &
                sleep 3
                print_success "Windows executable launched successfully"
            else
                print_error "Windows executable not found: $APP_PATH"
                exit 1
            fi
            ;;
        *)
            print_error "Unknown platform: $(uname -s)"
            exit 1
            ;;
    esac
    
    print_success "Application test completed"
}

# Main script logic
main() {
    print_status "WhisperEngine Build System"
    print_status "=========================="
    
    # Parse command
    COMMAND="${1:-build}"
    shift || true
    
    case "$COMMAND" in
        "build"|"build-all"|"clean"|"info")
            check_venv
            install_deps
            print_status "Running: python build_cross_platform.py $COMMAND $@"
            python build_cross_platform.py "$COMMAND" "$@"
            ;;
        "test")
            test_app
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"