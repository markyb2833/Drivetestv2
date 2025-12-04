# Debugging Bay Map Issues

## Quick Debug Steps

### 1. Check if drives are being detected

```bash
# Test drive detection directly
sudo python drive_detector.py

# Or check API
curl http://localhost:5005/api/drives
```

### 2. Check bay map API response

```bash
curl http://localhost:5005/api/bay-map | python -m json.tool
```

Look for:
- `drives_detected`: Number of drives found
- `bays_mapped`: Number of drives mapped to bays
- `bays`: Array of bay objects

### 3. Common Issues

**Issue: Drives detected but no bay numbers**
- SCSI info might not be readable
- Bay numbers come from SCSI target number
- Check: `ls -la /sys/block/sdX/device/scsi_device`

**Issue: No drives detected**
- Check if drives are being filtered as OS drive
- Verify: `lsblk` shows the drives
- Check: `sudo smartctl -i /dev/sdX` works

**Issue: Bay map empty**
- Drives might not have SCSI target numbers
- Solution: Configure backplane manually or fix SCSI detection

### 4. Manual Backplane Configuration

If automatic bay detection doesn't work, configure manually:

```python
# Via API
curl -X PUT http://localhost:5005/api/config/backplane \
  -H "Content-Type: application/json" \
  -d '{"total_bays": 24, "auto_detect": false}'
```

### 5. Check Backend Logs

Look for errors in the terminal where `app.py` is running:
- Drive detection errors
- SCSI reading errors
- Bay mapping errors

### 6. Test SCSI Detection

```bash
# Check if SCSI info is readable
cat /sys/block/sdb/device/scsi_device

# Or if it's a directory
ls -la /sys/block/sdb/device/scsi_device/

# Use udevadm as fallback
udevadm info --query=property --name=/dev/sdb | grep ID_SCSI
```

## Expected Behavior

- **With drives and bay mapping**: Shows bays with drive info
- **With drives but no bay mapping**: Shows drives without bay numbers (indexed 0, 1, 2...)
- **No drives**: Shows empty bays (at least 1 bay for testing)

## API Response Format

```json
{
  "success": true,
  "bays": [
    {
      "bay_number": 0,
      "occupied": true,
      "serial": "ABC123",
      "model": "Drive Model",
      ...
    },
    {
      "bay_number": 1,
      "occupied": false
    }
  ],
  "total_bays": 2,
  "occupied_bays": 1,
  "debug": {
    "drives_detected": 1,
    "bays_mapped": 1,
    "backplane_configured": false
  }
}
```

