#!/bin/bash
# WhisperEngine Release Helper Script
# Version: 1.2.0

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Get current version
get_current_version() {
    grep -E '^version = ' "$ROOT_DIR/pyproject.toml" | sed 's/version = "\(.*\)"/\1/'
}

# Validate git status
check_git_status() {
    if [[ $(git status --porcelain) ]]; then
        print_error "Working directory is not clean. Please commit or stash changes."
        exit 1
    fi
    print_success "Git working directory is clean"
}

# Validate tests
run_tests() {
    print_info "Running test suite..."
    cd "$ROOT_DIR"
    
    if command -v pytest &> /dev/null; then
        if pytest tests/ -m "not integration" --tb=short; then
            print_success "Unit tests passed"
        else
            print_error "Unit tests failed"
            exit 1
        fi
    else
        print_warning "pytest not found, skipping tests"
    fi
}

# Create git tag
create_tag() {
    local version=$1
    local tag="v$version"
    
    print_info "Creating git tag: $tag"
    
    # Create annotated tag with release notes
    git tag -a "$tag" -m "WhisperEngine $tag - Production Hardening Sprint

$(head -n 20 "$ROOT_DIR/RELEASE_NOTES.md")"
    
    print_success "Created tag: $tag"
    
    # Ask if user wants to push
    read -p "Push tag to origin? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin "$tag"
        print_success "Tag pushed to origin"
    else
        print_warning "Tag created locally only. Remember to push: git push origin $tag"
    fi
}

# Generate release artifacts
generate_artifacts() {
    print_info "Generating release artifacts..."
    
    # Create release directory
    mkdir -p "$ROOT_DIR/release-artifacts"
    
    # Copy key files
    cp "$ROOT_DIR/CHANGELOG.md" "$ROOT_DIR/release-artifacts/"
    cp "$ROOT_DIR/RELEASE_NOTES.md" "$ROOT_DIR/release-artifacts/"
    cp "$ROOT_DIR/README.md" "$ROOT_DIR/release-artifacts/"
    
    # Generate requirements summary
    echo "# WhisperEngine v$(get_current_version) - Requirements Summary" > "$ROOT_DIR/release-artifacts/REQUIREMENTS_SUMMARY.md"
    echo "" >> "$ROOT_DIR/release-artifacts/REQUIREMENTS_SUMMARY.md"
    echo "## Core Dependencies" >> "$ROOT_DIR/release-artifacts/REQUIREMENTS_SUMMARY.md"
    head -n 20 "$ROOT_DIR/requirements-core.txt" >> "$ROOT_DIR/release-artifacts/REQUIREMENTS_SUMMARY.md"
    
    print_success "Release artifacts generated in release-artifacts/"
}

# Main release function
main() {
    echo "🚀 WhisperEngine Release Helper"
    echo "==============================="
    
    local current_version
    current_version=$(get_current_version)
    
    print_info "Current version: $current_version"
    
    # Validate environment
    check_git_status
    
    # Run tests
    if [[ "${SKIP_TESTS:-}" != "true" ]]; then
        run_tests
    else
        print_warning "Skipping tests (SKIP_TESTS=true)"
    fi
    
    # Generate artifacts
    generate_artifacts
    
    # Create tag
    read -p "Create git tag for version $current_version? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_tag "$current_version"
    fi
    
    echo ""
    print_success "Release preparation complete!"
    echo ""
    print_info "Next steps:"
    echo "  1. Push changes: git push origin $(git branch --show-current)"
    echo "  2. Create GitHub release: https://github.com/whisperengine-ai/whisperengine/releases/new"
    echo "  3. Upload RELEASE_NOTES.md as release description"
    echo "  4. CI/CD will automatically:"
    echo "     - Build and sign containers"
    echo "     - Generate SBOM artifacts"
    echo "     - Publish to multiple registries"
    echo "     - Create deployment packages"
    echo ""
    print_info "Release artifacts available in: release-artifacts/"
}

# Handle arguments
case "${1:-}" in
    "test")
        run_tests
        ;;
    "tag")
        create_tag "$(get_current_version)"
        ;;
    "artifacts")
        generate_artifacts
        ;;
    *)
        main
        ;;
esac