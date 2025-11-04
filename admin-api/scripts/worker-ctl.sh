#!/bin/bash
# Fine-tuning Worker Control Script
# 시큐어 코딩: Input validation, error handling
# 유지보수성: Clear logging, modular functions

set -euo pipefail  # Fail on error, undefined variables, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
}

# Start the worker
start_worker() {
    log_info "Starting Celery Worker..."
    docker compose up -d celery-worker

    log_info "Waiting for worker to start..."
    sleep 5

    log_info "Checking worker status..."
    docker compose exec celery-worker celery -A app.core.celery_app inspect ping || {
        log_error "Worker failed to start. Check logs with: docker compose logs celery-worker"
        exit 1
    }

    log_info "Worker started successfully!"
}

# Stop the worker
stop_worker() {
    log_info "Stopping Celery Worker..."
    docker compose stop celery-worker
    log_info "Worker stopped."
}

# Restart the worker
restart_worker() {
    log_info "Restarting Celery Worker..."
    docker compose restart celery-worker

    log_info "Waiting for worker to restart..."
    sleep 5

    log_info "Checking worker status..."
    docker compose exec celery-worker celery -A app.core.celery_app inspect ping || {
        log_error "Worker failed to restart. Check logs with: docker compose logs celery-worker"
        exit 1
    }

    log_info "Worker restarted successfully!"
}

# Show worker logs
show_logs() {
    local lines="${1:-100}"  # Default 100 lines
    log_info "Showing last $lines lines of worker logs..."
    docker compose logs --tail="$lines" -f celery-worker
}

# Check worker status
check_status() {
    log_info "Checking Celery Worker status..."

    # Check if container is running
    if ! docker compose ps celery-worker | grep -q "Up"; then
        log_error "Worker container is not running."
        exit 1
    fi

    log_info "Container is running."

    # Check Celery status
    log_info "Checking Celery worker..."
    docker compose exec celery-worker celery -A app.core.celery_app inspect ping || {
        log_error "Celery worker is not responding."
        exit 1
    }

    # Show active tasks
    log_info "\nActive tasks:"
    docker compose exec celery-worker celery -A app.core.celery_app inspect active || true

    # Show registered tasks
    log_info "\nRegistered tasks:"
    docker compose exec celery-worker celery -A app.core.celery_app inspect registered || true

    log_info "\n${GREEN}Worker is healthy!${NC}"
}

# Show GPU status
check_gpu() {
    log_info "Checking GPU availability..."
    docker compose exec celery-worker nvidia-smi || {
        log_error "GPU not accessible in worker container."
        exit 1
    }
}

# Purge all tasks in queue
purge_queue() {
    log_warn "This will delete ALL pending tasks in the queue!"
    read -p "Are you sure? (yes/no): " -r

    if [[ "$REPLY" == "yes" ]]; then
        log_info "Purging Celery queue..."
        docker compose exec celery-worker celery -A app.core.celery_app purge -f
        log_info "Queue purged."
    else
        log_info "Operation cancelled."
    fi
}

# Show help
show_help() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
    start           Start the Celery worker
    stop            Stop the Celery worker
    restart         Restart the Celery worker
    status          Check worker status and show active tasks
    logs [lines]    Show worker logs (default: 100 lines)
    gpu             Check GPU availability
    purge           Purge all pending tasks (DANGEROUS!)
    help            Show this help message

Examples:
    $0 start
    $0 logs 200
    $0 status
    $0 gpu

EOF
}

# Main command dispatcher
main() {
    check_docker_compose

    local command="${1:-help}"

    case "$command" in
        start)
            start_worker
            ;;
        stop)
            stop_worker
            ;;
        restart)
            restart_worker
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs "${2:-100}"
            ;;
        gpu)
            check_gpu
            ;;
        purge)
            purge_queue
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
