.PHONY: install start stop status clean help

# Default target
help:
	@echo "Avalytics Backend - AvalancheGo Node Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make install    - Download and install AvalancheGo binary"
	@echo "  make start      - Start the AvalancheGo node"
	@echo "  make stop       - Stop the AvalancheGo node"
	@echo "  make status     - Check node health and status"
	@echo "  make clean      - Remove installed binaries and data"
	@echo "  make help       - Show this help message"

install:
	@./scripts/install.sh

start:
	@./scripts/start.sh

stop:
	@./scripts/stop.sh

status:
	@./scripts/status.sh

clean:
	@echo "Cleaning up..."
	@rm -rf bin/avalanchego*
	@rm -rf data/db
	@echo "✅ Clean complete"


