# HDSentinel Location Guide

## Where to Place HDSentinel Binary

The install script and Python integration will look for HDSentinel in these locations (in order):

1. **System PATH** - `/usr/local/bin/hdsentinel` or `/usr/bin/hdsentinel`
2. **Project root** - `./hdsentinel` (same directory as install.sh)
3. **Tools directory** - `./tools/hdsentinel`
4. **Opt directory** - `/opt/hdsentinel/hdsentinel`

## Quick Setup

If you have the HDSentinel binary file:

```bash
# Option 1: Place in project root
cp /path/to/hdsentinel ./hdsentinel
chmod +x ./hdsentinel

# Option 2: Place in tools directory
mkdir -p tools
cp /path/to/hdsentinel ./tools/hdsentinel
chmod +x ./tools/hdsentinel

# Option 3: Install system-wide (recommended for production)
sudo cp /path/to/hdsentinel /usr/local/bin/hdsentinel
sudo chmod +x /usr/local/bin/hdsentinel
```

## Verify Detection

After placing HDSentinel, run:

```bash
# Check if install script detects it
./install.sh

# Or test Python integration
python3 -c "from hdsentinel_integration import HDSentinelIntegration; h = HDSentinelIntegration(); print('Found:', h.hdsentinel_path)"
```

## File Permissions

Make sure HDSentinel is executable:

```bash
chmod +x hdsentinel
# or
chmod +x ./tools/hdsentinel
```

## Troubleshooting

**If install script says "NOT FOUND":**
1. Check file exists: `ls -la ./hdsentinel`
2. Check it's executable: `chmod +x ./hdsentinel`
3. Check file name is exactly `hdsentinel` (case-sensitive)
4. Run install script from project root directory

**If Python can't find it:**
- The integration searches the same locations
- Make sure you're running Python from the project root
- Check file permissions: `ls -l ./hdsentinel`

