#!/bin/bash
# =============================================================================
# WhisperEngine Automated Backup Scheduler
# =============================================================================
# Simple cron-based backup scheduler for regular automated backups
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"
CRON_COMMENT="# WhisperEngine automated backup"

# Check if backup script exists
check_backup_script() {
    if [[ ! -f "$BACKUP_SCRIPT" ]]; then
        print_error "Backup script not found: $BACKUP_SCRIPT"
        exit 1
    fi
    
    if [[ ! -x "$BACKUP_SCRIPT" ]]; then
        chmod +x "$BACKUP_SCRIPT"
    fi
}

# Install automated backup to cron
install_cron_backup() {
    local schedule="${1:-daily}"
    local cleanup_days="${2:-30}"
    
    echo "📅 Installing automated backup schedule"
    echo "======================================="
    echo "Schedule: $schedule"
    echo "Cleanup: Remove backups older than $cleanup_days days"
    echo ""
    
    check_backup_script
    
    # Convert schedule to cron expression
    local cron_expr=""
    case "$schedule" in
        "hourly")
            cron_expr="0 * * * *"
            ;;
        "daily")
            cron_expr="0 2 * * *"  # 2 AM daily
            ;;
        "weekly")
            cron_expr="0 2 * * 0"  # 2 AM every Sunday
            ;;
        "monthly")
            cron_expr="0 2 1 * *"  # 2 AM on 1st of each month
            ;;
        *)
            if [[ "$schedule" =~ ^[0-9\ \*]+$ ]]; then
                # Custom cron expression
                cron_expr="$schedule"
            else
                print_error "Invalid schedule: $schedule"
                echo "Valid options: hourly, daily, weekly, monthly, or custom cron expression"
                exit 1
            fi
            ;;
    esac
    
    # Create backup command
    local backup_cmd="cd $PROJECT_ROOT && $BACKUP_SCRIPT create >/dev/null 2>&1"
    local cleanup_cmd="cd $PROJECT_ROOT && $BACKUP_SCRIPT cleanup $cleanup_days >/dev/null 2>&1"
    
    # Remove existing WhisperEngine backup cron jobs
    crontab -l 2>/dev/null | grep -v "$CRON_COMMENT" | crontab - 2>/dev/null || true
    
    # Add new cron jobs
    (
        crontab -l 2>/dev/null || true
        echo "$CRON_COMMENT - backup"
        echo "$cron_expr $backup_cmd"
        echo "$CRON_COMMENT - cleanup"
        echo "0 3 * * 0 $cleanup_cmd"  # Weekly cleanup at 3 AM Sunday
    ) | crontab -
    
    print_status "Automated backup installed successfully!"
    echo ""
    echo "📋 Backup Schedule:"
    echo "   Frequency: $schedule"
    echo "   Cron: $cron_expr"
    echo "   Time: $(echo "$cron_expr" | awk '{print $2":"$1}' 2>/dev/null || echo "Custom schedule")"
    echo ""
    echo "🧹 Cleanup Schedule:"
    echo "   Frequency: Weekly (Sundays at 3 AM)"
    echo "   Retention: $cleanup_days days"
    echo ""
    echo "🔍 To view current cron jobs:"
    echo "   crontab -l"
    echo ""
    echo "🛑 To remove automated backups:"
    echo "   $0 uninstall"
}

# Remove automated backup from cron
uninstall_cron_backup() {
    echo "🛑 Removing automated backup schedule"
    echo "====================================="
    
    # Check if any WhisperEngine cron jobs exist
    if crontab -l 2>/dev/null | grep -q "$CRON_COMMENT"; then
        # Remove WhisperEngine backup cron jobs
        crontab -l 2>/dev/null | grep -v "$CRON_COMMENT" | crontab - 2>/dev/null || true
        print_status "Automated backup schedule removed"
    else
        print_warning "No automated backup schedule found"
    fi
}

# Show current cron status
show_cron_status() {
    echo "📅 Automated Backup Status"
    echo "=========================="
    echo ""
    
    if crontab -l 2>/dev/null | grep -q "$CRON_COMMENT"; then
        echo "✅ Automated backups are ENABLED"
        echo ""
        echo "Current schedule:"
        crontab -l 2>/dev/null | grep -A1 "$CRON_COMMENT" | grep -v "$CRON_COMMENT" | while read -r line; do
            if [[ -n "$line" ]]; then
                local cron_time=$(echo "$line" | awk '{print $1" "$2" "$3" "$4" "$5}')
                local cron_cmd=$(echo "$line" | awk '{for(i=6;i<=NF;i++) printf $i" "; print ""}')
                echo "   • $cron_time - $cron_cmd"
            fi
        done
        echo ""
    else
        echo "❌ Automated backups are DISABLED"
        echo ""
        echo "To enable automated backups:"
        echo "   $0 install [daily|weekly|monthly]"
        echo ""
    fi
    
    # Show recent backup activity
    if [[ -d "$PROJECT_ROOT/backups" ]]; then
        echo "📁 Recent Backup Activity:"
        local backup_count=$(find "$PROJECT_ROOT/backups" -name "whisperengine_backup_*" -type d 2>/dev/null | wc -l | tr -d ' ')
        if [[ $backup_count -gt 0 ]]; then
            echo "   Total backups: $backup_count"
            local latest_backup=$(find "$PROJECT_ROOT/backups" -name "whisperengine_backup_*" -type d 2>/dev/null | sort | tail -1)
            if [[ -n "$latest_backup" ]]; then
                local latest_name=$(basename "$latest_backup")
                local latest_timestamp=${latest_name#whisperengine_backup_}
                local latest_date=$(date -j -f "%Y%m%d_%H%M%S" "$latest_timestamp" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$latest_timestamp")
                echo "   Latest backup: $latest_date"
            fi
        else
            echo "   No backups found"
        fi
    fi
}

# Manual backup trigger (for testing)
trigger_backup() {
    echo "🚀 Manually triggering backup..."
    echo "================================"
    
    check_backup_script
    
    cd "$PROJECT_ROOT"
    exec "$BACKUP_SCRIPT" create
}

# Show help
show_help() {
    echo "WhisperEngine Automated Backup Scheduler"
    echo "========================================"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  install [schedule] [cleanup_days]  - Install automated backup"
    echo "  uninstall                          - Remove automated backup"
    echo "  status                             - Show current backup status"
    echo "  trigger                            - Manually trigger a backup"
    echo "  help                               - Show this help message"
    echo ""
    echo "Schedule Options:"
    echo "  hourly     - Every hour"
    echo "  daily      - Daily at 2 AM (default)"
    echo "  weekly     - Weekly on Sunday at 2 AM"
    echo "  monthly    - Monthly on 1st at 2 AM"
    echo "  \"CRON\"     - Custom cron expression (quoted)"
    echo ""
    echo "Examples:"
    echo "  $0 install daily                 # Daily backups at 2 AM"
    echo "  $0 install weekly 14             # Weekly backups, keep 14 days"
    echo "  $0 install \"0 4 * * *\"           # Daily at 4 AM (custom cron)"
    echo "  $0 status                        # Check current status"
    echo "  $0 uninstall                     # Remove automation"
    echo ""
    echo "Notes:"
    echo "  • Automatic cleanup runs weekly (Sundays at 3 AM)"
    echo "  • Default retention is 30 days"
    echo "  • Requires cron service to be running"
    echo ""
}

# Main command handling
case "${1:-help}" in
    "install")
        install_cron_backup "${2:-daily}" "${3:-30}"
        ;;
    "uninstall")
        uninstall_cron_backup
        ;;
    "status")
        show_cron_status
        ;;
    "trigger")
        trigger_backup
        ;;
    "help"|*)
        show_help
        ;;
esac