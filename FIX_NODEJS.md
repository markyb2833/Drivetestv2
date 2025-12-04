# Fix Node.js Installation

## Quick Fix

If Node.js is not installed, run:

```bash
# Option 1: Use the standalone script
chmod +x install_nodejs.sh
./install_nodejs.sh

# Option 2: Manual installation
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version
npm --version
```

## Updated install.sh

The `install.sh` script has been updated to automatically install Node.js if it's missing. You can:

1. **Pull the latest changes:**
   ```bash
   git pull
   ```

2. **Re-run install.sh:**
   ```bash
   ./install.sh
   ```

The script will now detect missing Node.js and install it automatically.

## After Installing Node.js

Once Node.js is installed:

1. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Build frontend (for production):**
   ```bash
   npm run build
   ```

3. **Or run frontend dev server:**
   ```bash
   npm start
   ```

## Verification

Check that everything is working:

```bash
node --version    # Should show v18.x.x or higher
npm --version     # Should show version number
```

