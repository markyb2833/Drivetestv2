#!/bin/bash
#
# Auto-install script for HDD Tester Platform
# Installs all Python, Node.js, and system dependencies
#

# Don't exit on error - continue with warnings
# set -e  # Exit on error

echo "=========================================="
echo "HDD Tester Platform - Auto Install"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root for system packages
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Note: Some system packages may require sudo.${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
else
    echo -e "${RED}Cannot detect OS. Assuming Ubuntu/Debian.${NC}"
    OS="ubuntu"
fi

echo -e "${GREEN}Detected OS: $OS $OS_VERSION${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system package
install_system_package() {
    local pkg=$1
    if command_exists "$pkg"; then
        echo -e "${GREEN}✓${NC} $pkg already installed"
        return 0
    fi
    
    echo -e "${YELLOW}Installing $pkg...${NC}"
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        $SUDO apt-get update -qq
        $SUDO apt-get install -y "$pkg" >/dev/null 2>&1 || {
            echo -e "${RED}✗ Failed to install $pkg${NC}"
            return 1
        }
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        $SUDO yum install -y "$pkg" >/dev/null 2>&1 || {
            echo -e "${RED}✗ Failed to install $pkg${NC}"
            return 1
        }
    else
        echo -e "${RED}✗ Unsupported OS for automatic package installation${NC}"
        echo "Please install $pkg manually"
        return 1
    fi
    echo -e "${GREEN}✓${NC} $pkg installed"
}

# ============================================================================
# System Dependencies
# ============================================================================
echo "=========================================="
echo "Installing System Dependencies"
echo "=========================================="

SYSTEM_PACKAGES=(
    "smartmontools"      # smartctl for SMART monitoring
    "hdparm"             # Hard disk utilities
    "util-linux"         # lsblk, blockdev
    "sg3-utils"          # sg_scan, sg_map for SCSI/SAS
    "python3"             # Python 3
    "python3-pip"         # pip
    "python3-venv"        # venv module
    "nodejs"              # Node.js (if available)
    "npm"                 # npm
    "build-essential"     # Build tools (for some Python packages)
    "wget"                # For downloading HDSentinel
    "curl"                # For downloading HDSentinel
)

for pkg in "${SYSTEM_PACKAGES[@]}"; do
    install_system_package "$pkg" || true
done

# Install Node.js if not found or version is too old
if ! command_exists node; then
    echo -e "${YELLOW}Node.js not found. Installing Node.js 18.x LTS...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | $SUDO bash -
    $SUDO apt-get install -y nodejs
    echo -e "${GREEN}✓${NC} Node.js installed"
elif command_exists node; then
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 14 ]; then
        echo -e "${YELLOW}Node.js version is too old ($(node -v)). Installing Node.js 18.x...${NC}"
        curl -fsSL https://deb.nodesource.com/setup_18.x | $SUDO bash -
        $SUDO apt-get install -y nodejs
        echo -e "${GREEN}✓${NC} Node.js updated"
    else
        echo -e "${GREEN}✓${NC} Node.js $(node -v) already installed"
    fi
fi

echo ""

# ============================================================================
# Python Virtual Environment
# ============================================================================
echo "=========================================="
echo "Setting up Python Virtual Environment"
echo "=========================================="

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo ""

# ============================================================================
# Python Dependencies
# ============================================================================
echo "=========================================="
echo "Installing Python Dependencies"
echo "=========================================="

if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install --upgrade pip >/dev/null 2>&1
    pip install -r requirements.txt
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
fi

echo ""

# ============================================================================
# Node.js Dependencies
# ============================================================================
echo "=========================================="
echo "Installing Node.js Dependencies"
echo "=========================================="

if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        echo "Installing npm packages..."
        npm install
        echo -e "${GREEN}✓${NC} Node.js dependencies installed"
    else
        echo -e "${YELLOW}⚠ package.json not found in frontend/${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠ frontend directory not found${NC}"
fi

echo ""

# ============================================================================
# Database Setup
# ============================================================================
echo "=========================================="
echo "Database Setup"
echo "=========================================="

echo "Note: MySQL database should be accessible at:"
echo "mysql://newinv:password123!@192.168.0.197/compudrive"
echo ""
echo "To initialize database tables, run:"
echo "  source venv/bin/activate"
echo "  python init_database.py"
echo ""

# ============================================================================
# Verification
# ============================================================================
echo "=========================================="
echo "Verification"
echo "=========================================="

# Check critical tools
CRITICAL_TOOLS=("smartctl" "hdparm" "lsblk" "python3" "node")
OPTIONAL_TOOLS=("hdsentinel")
ALL_GOOD=true

for tool in "${CRITICAL_TOOLS[@]}"; do
    if command_exists "$tool"; then
        VERSION=$($tool --version 2>/dev/null | head -n1 || echo "installed")
        echo -e "${GREEN}✓${NC} $tool: $VERSION"
    else
        echo -e "${RED}✗${NC} $tool: NOT FOUND"
        ALL_GOOD=false
    fi
done

echo ""
echo "Optional tools:"
for tool in "${OPTIONAL_TOOLS[@]}"; do
    if [ "$tool" = "hdsentinel" ]; then
        # Check for HDSentinel in multiple locations
        HDSENTINEL_FOUND=false
        HDSENTINEL_PATH=""
        
        # Check common system locations
        if command_exists "$tool"; then
            HDSENTINEL_PATH=$(which "$tool")
            HDSENTINEL_FOUND=true
        # Check project directory locations
        elif [ -f "./hdsentinel" ] && [ -x "./hdsentinel" ]; then
            HDSENTINEL_PATH="./hdsentinel"
            HDSENTINEL_FOUND=true
        elif [ -f "./tools/hdsentinel" ] && [ -x "./tools/hdsentinel" ]; then
            HDSENTINEL_PATH="./tools/hdsentinel"
            HDSENTINEL_FOUND=true
        elif [ -f "hdsentinel" ] && [ -x "hdsentinel" ]; then
            HDSENTINEL_PATH="hdsentinel"
            HDSENTINEL_FOUND=true
        fi
        
        if [ "$HDSENTINEL_FOUND" = true ]; then
            VERSION=$($HDSENTINEL_PATH --version 2>/dev/null | head -n1 || echo "installed")
            echo -e "${GREEN}✓${NC} $tool: Found at $HDSENTINEL_PATH ($VERSION)"
        else
            echo -e "${YELLOW}⚠${NC} $tool: NOT FOUND (optional, but recommended)"
            echo "   Place HDSentinel binary in: ./hdsentinel or ./tools/hdsentinel"
        fi
    else
        if command_exists "$tool"; then
            VERSION=$($tool --version 2>/dev/null | head -n1 || echo "installed")
            echo -e "${GREEN}✓${NC} $tool: $VERSION"
        else
            echo -e "${YELLOW}⚠${NC} $tool: NOT FOUND (optional, but recommended)"
        fi
    fi
done

echo ""

# ============================================================================
# Summary
# ============================================================================
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}=========================================="
    echo "Installation Complete!"
    echo "==========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Initialize database:"
    echo "   python init_database.py"
    echo ""
    echo "3. Start backend:"
    echo "   python app.py"
    echo ""
    echo "4. Start frontend (in another terminal):"
    echo "   cd frontend && npm start"
    echo ""
else
    echo -e "${YELLOW}=========================================="
    echo "Installation completed with warnings"
    echo "==========================================${NC}"
    echo ""
    echo "Some tools are missing. Please install them manually."
    echo ""
fi

