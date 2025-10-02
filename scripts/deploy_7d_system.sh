#!/bin/bash

# 🚀 Enhanced 7D Vector System - Automated Deployment Script
# WhisperEngine Character Migration to 7D Intelligence

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
WORKSPACE_ROOT="/Users/markcastillo/git/whisperengine"
BACKUP_DIR="$WORKSPACE_ROOT/backups/7d_migration_$(date +%Y%m%d_%H%M%S)"

# Available characters
ALL_CHARACTERS=("elena" "marcus" "jake" "ryan" "gabriel" "dream" "sophia" "aethys")
PRIORITY_CHARACTERS=("elena" "jake" "ryan" "gabriel")  # Phase 4 testing priorities

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE} 7D Vector System Deployment${NC}"
    echo -e "${PURPLE}================================${NC}"
    echo ""
}

print_section() {
    echo -e "${BLUE}▶ $1${NC}"
    echo ""
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

check_prerequisites() {
    print_section "Checking Prerequisites"
    
    # Check if in correct directory
    if [[ ! -f "multi-bot.sh" ]]; then
        print_error "Must run from WhisperEngine root directory"
        exit 1
    fi
    
    # Check if Qdrant is running
    if ! docker ps | grep -q qdrant; then
        print_error "Qdrant container not running. Start infrastructure first."
        exit 1
    fi
    
    # Check if virtual environment exists
    if [[ ! -d ".venv" ]]; then
        print_error "Python virtual environment not found. Run 'python -m venv .venv' first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
    echo ""
}

backup_environment() {
    print_section "Creating Environment Backup"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup environment files
    for char in "${ALL_CHARACTERS[@]}"; do
        if [[ -f ".env.$char" ]]; then
            cp ".env.$char" "$BACKUP_DIR/.env.$char.backup"
            print_success "Backed up .env.$char"
        fi
    done
    
    echo ""
    print_success "Environment backup created at: $BACKUP_DIR"
    echo ""
}

update_character_env() {
    local character=$1
    local env_file=".env.$character"
    
    if [[ ! -f "$env_file" ]]; then
        print_warning "Environment file $env_file not found, skipping $character"
        return 1
    fi
    
    # Check if already using 7D collection
    if grep -q "_7d" "$env_file"; then
        print_warning "$character already using 7D collection"
        return 0
    fi
    
    # Update collection name for 7D
    if grep -q "QDRANT_COLLECTION_NAME=" "$env_file"; then
        # Handle special case for Aethys
        if [[ "$character" == "aethys" ]]; then
            sed -i '' 's/QDRANT_COLLECTION_NAME=chat_memories_aethys/QDRANT_COLLECTION_NAME=chat_memories_aethys_7d/' "$env_file"
        else
            sed -i '' "s/QDRANT_COLLECTION_NAME=whisperengine_memory_$character/QDRANT_COLLECTION_NAME=whisperengine_memory_${character}_7d/" "$env_file"
        fi
        print_success "Updated $character to use 7D collection"
        return 0
    else
        print_error "QDRANT_COLLECTION_NAME not found in $env_file"
        return 1
    fi
}

deploy_character() {
    local character=$1
    local phase=$2
    
    print_section "Deploying $character ($phase)"
    
    # Check if character has existing memories
    local source_collection="whisperengine_memory_$character"
    if [[ "$character" == "aethys" ]]; then
        source_collection="chat_memories_aethys"
    fi
    
    local memory_count
    memory_count=$(curl -s "http://localhost:6334/collections/$source_collection" | jq -r '.result.points_count // 0')
    
    if [[ "$memory_count" -gt 0 ]]; then
        echo ""
        print_warning "$character has $memory_count existing memories in $source_collection"
        echo ""
        echo "🤖 IMPORTANT: Users won't remember conversations with $character unless memories are migrated!"
        echo ""
        echo "Options:"
        echo "1. Deploy with fresh 7D collection (users lose conversation history)"
        echo "2. Migrate existing memories to 7D format (preserves user relationships)"
        echo "3. Cancel deployment"
        echo ""
        read -p "Choose option (1/2/3): " migration_choice
        
        case "$migration_choice" in
            "1")
                print_warning "Proceeding with fresh 7D collection - users will lose conversation history"
                ;;
            "2")
                print_section "Starting memory migration for $character"
                echo "This will migrate $memory_count memories to 7D format..."
                echo "⚠️  This may take several minutes for large memory collections"
                read -p "Continue with migration? (y/N): " confirm_migration
                
                if [[ "$confirm_migration" =~ ^[Yy]$ ]]; then
                    echo "🚀 Starting memory migration (this may take a while)..."
                    
                    # Run memory migration (limit to 1000 memories for safety)
                    cd "$WORKSPACE_ROOT"
                    source .venv/bin/activate
                    
                    if python scripts/migrate_3d_to_7d_memories.py "$character" --max-memories 1000; then
                        print_success "Memory migration completed successfully"
                    else
                        print_error "Memory migration failed"
                        read -p "Continue with fresh collection anyway? (y/N): " continue_anyway
                        if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
                            print_error "Deployment cancelled"
                            return 1
                        fi
                    fi
                else
                    print_error "Migration cancelled - deploying with fresh collection"
                fi
                ;;
            "3")
                print_error "Deployment cancelled by user"
                return 1
                ;;
            *)
                print_error "Invalid choice - deployment cancelled"
                return 1
                ;;
        esac
    fi
    
    # Update environment
    if ! update_character_env "$character"; then
        return 1
    fi
    
    # Stop character if running
    echo "Stopping $character..."
    ./multi-bot.sh stop "$character" &>/dev/null || true
    
    # Wait a moment for clean shutdown
    sleep 2
    
    # Start character with 7D system
    echo "Starting $character with 7D system..."
    if ./multi-bot.sh start "$character"; then
        print_success "$character deployed successfully"
        
        # Wait for startup
        sleep 5
        
        # Check if container is healthy
        if docker ps | grep -q "whisperengine-$character-bot"; then
            print_success "$character container is running"
            
            # Quick health check
            local port
            case "$character" in
                "elena") port=9091 ;;
                "marcus") port=9092 ;;
                "ryan") port=9093 ;;
                "dream") port=9094 ;;
                "gabriel") port=9095 ;;
                "sophia") port=9096 ;;
                "jake") port=9097 ;;
                "aethys") port=3007 ;;
            esac
            
            if curl -s "http://localhost:$port/health" &>/dev/null; then
                print_success "$character health check passed"
            else
                print_warning "$character health check failed (may still be starting)"
            fi
        else
            print_error "$character container failed to start"
            return 1
        fi
    else
        print_error "Failed to start $character"
        return 1
    fi
    
    echo ""
    return 0
}

validate_7d_system() {
    print_section "Validating 7D System"
    
    cd "$WORKSPACE_ROOT"
    source .venv/bin/activate
    
    # Test 7D analyzer
    echo "Testing 7D analyzer functionality..."
    if python test_7d_quick.py &>/dev/null; then
        print_success "7D analyzer test passed"
    else
        print_warning "7D analyzer test had issues (check manually)"
    fi
    
    # Check Qdrant collections
    echo "Checking Qdrant collections..."
    if curl -s http://localhost:6334/collections | grep -q "_7d"; then
        print_success "7D collections created successfully"
    else
        print_warning "No 7D collections found yet (may be created on first use)"
    fi
    
    echo ""
}

rollback_character() {
    local character=$1
    
    print_section "Rolling back $character to 3D system"
    
    local env_file=".env.$character"
    
    if [[ -f "$env_file" ]]; then
        # Remove _7d suffix from collection name
        if [[ "$character" == "aethys" ]]; then
            sed -i '' 's/QDRANT_COLLECTION_NAME=chat_memories_aethys_7d/QDRANT_COLLECTION_NAME=chat_memories_aethys/' "$env_file"
        else
            sed -i '' "s/QDRANT_COLLECTION_NAME=whisperengine_memory_${character}_7d/QDRANT_COLLECTION_NAME=whisperengine_memory_${character}/" "$env_file"
        fi
        
        # Restart character
        ./multi-bot.sh stop "$character" &>/dev/null || true
        sleep 2
        ./multi-bot.sh start "$character"
        
        print_success "$character rolled back to 3D system"
    else
        print_error "Environment file for $character not found"
    fi
}

show_usage() {
    echo "Usage: $0 [command] [character]"
    echo ""
    echo "Commands:"
    echo "  deploy-elena     Deploy to Elena for validation"
    echo "  deploy-priority  Deploy to priority characters (Elena, Jake, Ryan, Gabriel)"
    echo "  deploy-all       Deploy to all characters"
    echo "  deploy [char]    Deploy to specific character"
    echo "  rollback [char]  Rollback specific character to 3D"
    echo "  rollback-all     Rollback all characters to 3D"
    echo "  status          Show deployment status"
    echo ""
    echo "Characters: ${ALL_CHARACTERS[*]}"
}

show_status() {
    print_section "7D Deployment Status"
    
    for character in "${ALL_CHARACTERS[@]}"; do
        local env_file=".env.$character"
        if [[ -f "$env_file" ]]; then
            if grep -q "_7d" "$env_file"; then
                if docker ps | grep -q "whisperengine-$character-bot"; then
                    print_success "$character: 7D deployed and running"
                else
                    print_warning "$character: 7D configured but not running"
                fi
            else
                if docker ps | grep -q "whisperengine-$character-bot"; then
                    echo -e "${NC}$character: 3D system (running)"
                else
                    echo -e "${NC}$character: 3D system (stopped)"
                fi
            fi
        else
            echo -e "${NC}$character: No environment file"
        fi
    done
    echo ""
}

main() {
    print_header
    
    case "${1:-}" in
        "deploy-elena")
            check_prerequisites
            backup_environment
            deploy_character "elena" "Validation Phase"
            validate_7d_system
            echo -e "${GREEN}✨ Elena deployment complete! Test with Discord messages to validate 7D performance.${NC}"
            ;;
            
        "deploy-priority")
            check_prerequisites
            backup_environment
            
            echo -e "${YELLOW}Deploying priority characters based on Phase 4 testing results...${NC}"
            echo ""
            
            for character in "${PRIORITY_CHARACTERS[@]}"; do
                deploy_character "$character" "Priority Phase"
            done
            
            validate_7d_system
            echo -e "${GREEN}✨ Priority character deployment complete!${NC}"
            echo -e "${BLUE}Test each character with Phase 4 test scenarios to validate improvements.${NC}"
            ;;
            
        "deploy-all")
            check_prerequisites
            backup_environment
            
            echo -e "${YELLOW}Deploying all characters to 7D system...${NC}"
            echo ""
            
            for character in "${ALL_CHARACTERS[@]}"; do
                deploy_character "$character" "Full Rollout"
            done
            
            validate_7d_system
            echo -e "${GREEN}✨ Full 7D deployment complete!${NC}"
            ;;
            
        "deploy")
            if [[ -z "${2:-}" ]]; then
                print_error "Please specify a character to deploy"
                show_usage
                exit 1
            fi
            
            character="$2"
            if [[ ! " ${ALL_CHARACTERS[*]} " =~ " $character " ]]; then
                print_error "Unknown character: $character"
                show_usage
                exit 1
            fi
            
            check_prerequisites
            backup_environment
            deploy_character "$character" "Individual Deployment"
            validate_7d_system
            ;;
            
        "rollback")
            if [[ -z "${2:-}" ]]; then
                print_error "Please specify a character to rollback"
                show_usage
                exit 1
            fi
            
            character="$2"
            if [[ ! " ${ALL_CHARACTERS[*]} " =~ " $character " ]]; then
                print_error "Unknown character: $character"
                show_usage
                exit 1
            fi
            
            rollback_character "$character"
            ;;
            
        "rollback-all")
            echo -e "${YELLOW}Rolling back all characters to 3D system...${NC}"
            for character in "${ALL_CHARACTERS[@]}"; do
                rollback_character "$character"
            done
            echo -e "${GREEN}✨ All characters rolled back to 3D system${NC}"
            ;;
            
        "status")
            show_status
            ;;
            
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"