#!/bin/bash
# Install AvalancheGo binary for Avalytics backend
# Supports Linux and macOS

set -e

VERSION="v1.11.3"
INSTALL_DIR="${INSTALL_DIR:-./bin}"
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Map architecture
case $ARCH in
    x86_64)
        ARCH="amd64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Create install directory
mkdir -p "$INSTALL_DIR"

echo "Installing AvalancheGo ${VERSION} for ${OS}/${ARCH}..."

# Download binary
BINARY_URL="https://github.com/ava-labs/avalanchego/releases/download/${VERSION}/avalanchego-linux-${ARCH}-${VERSION}.tar.gz"
if [ "$OS" = "darwin" ]; then
    BINARY_URL="https://github.com/ava-labs/avalanchego/releases/download/${VERSION}/avalanchego-macos-${ARCH}-${VERSION}.zip"
fi

cd "$INSTALL_DIR"

if [ "$OS" = "darwin" ]; then
    curl -L "$BINARY_URL" -o avalanchego.zip
    unzip -q avalanchego.zip
    rm avalanchego.zip
else
    curl -L "$BINARY_URL" -o avalanchego.tar.gz
    tar -xzf avalanchego.tar.gz
    rm avalanchego.tar.gz
fi

# Make executable
chmod +x avalanchego*

echo "AvalancheGo installed successfully!"
echo "Binary location: $(pwd)/avalanchego"
echo ""
echo "To start the node, run:"
echo "  ./scripts/start.sh"


