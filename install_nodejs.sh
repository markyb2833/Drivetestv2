#!/bin/bash
#
# Install Node.js on Ubuntu/Debian
#

set -e

echo "Installing Node.js..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="ubuntu"
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    SUDO="sudo"
else
    SUDO=""
fi

# Install Node.js 18.x LTS
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    echo "Installing Node.js 18.x LTS..."
    
    # Remove old Node.js if exists
    $SUDO apt-get remove -y nodejs npm 2>/dev/null || true
    
    # Install Node.js 18.x from NodeSource
    curl -fsSL https://deb.nodesource.com/setup_18.x | $SUDO -E bash -
    $SUDO apt-get install -y nodejs
    
    # Verify installation
    node --version
    npm --version
    
    echo "✓ Node.js installed successfully"
else
    echo "Unsupported OS. Please install Node.js manually."
    exit 1
fi

