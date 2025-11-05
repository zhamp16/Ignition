# Timeout Troubleshooting Guide

## Common Error: "Idle timeout expired: 30009/30000 ms"

This error occurs when the OPC browsing operation takes longer than Ignition's default timeout (30 seconds).

### Version 2.0 Improvements

The updated script includes several timeout fixes:

1. **Retry Logic**: Automatic retry on OPC browse failures (3 attempts with 2-second delays)
2. **Progress Updates**: Regular progress messages every 5 seconds to keep the connection alive
3. **Chunked Processing**: Tags are created in batches to prevent timeouts during tag creation
4. **Better Error Recovery**: Individual failures don't stop the entire import

### Quick Fixes

#### Option 1: Reduce the Browsing Scope (Recommended)

Instead of browsing from a high-level path, target a more specific path:

```python
# Instead of this (broad scope):
BASE_OPC_PATH = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/'

# Use this (narrow scope):
BASE_OPC_PATH = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/'
```

#### Option 2: Adjust Chunk Size

If timeout occurs during tag creation, reduce the chunk size:

```python
# More reliable for slow connections
CHUNK_SIZE = 25  # Instead of default 50

# Or even smaller for very slow systems
CHUNK_SIZE = 10
```

#### Option 3: Import in Batches

For very large structures, import different tag types separately:

```python
# First run - CV tags only
SEARCH_TAG_NAME = 'CV'
result = main()

# Second run - PV tags only
SEARCH_TAG_NAME = 'PV'
result = main()

# Third run - SP tags only
SEARCH_TAG_NAME = 'SP'
result = main()
```

### Advanced Solutions

#### Solution 1: Increase Gateway Timeout

Edit Ignition's gateway settings to increase the script timeout:

1. Open Gateway webpage (http://localhost:8088)
2. Go to **Config** > **Gateway Settings** > **Security**
3. Increase **Script Execution Timeout** (default is 30 seconds)
4. Restart the gateway

**Warning**: This affects all scripts globally.

#### Solution 2: Use Gateway Event Scripts

Instead of running from the Script Console, use a Gateway Event Script which has no timeout:

1. In Designer, go to **Project** > **Gateway Events**
2. Create a new **Startup** script
3. Paste the import script code
4. Configure to run once
5. Save the project
6. Check the Gateway logs for output

#### Solution 3: Break Into Multiple Phases

Separate browsing from tag creation:

```python
# Phase 1: Browse and save results to database or file
found_tags = browse_opc_recursive(opc_server, base_opc_path, search_tag_name)
# Save found_tags to a dataset or internal tag for later use

# Phase 2: Create tags from saved results (run separately)
# Load found_tags from storage
for tag_info in found_tags:
    create_tag(...)
```

### Debugging Steps

#### Step 1: Test OPC Connection

Before running the full import, test your OPC connection:

```python
# Simple OPC browse test
opc_server = 'DeltaVEdge'
test_path = 'nsu=http://inmation.com/UA/;s=/System/Core'

try:
    results = system.opc.browse(opc_server, test_path)
    print("Connection successful! Found " + str(len(results)) + " items")
    for r in results:
        print("  - " + r.getDisplayName())
except Exception as e:
    print("Connection failed: " + str(e))
```

#### Step 2: Check OPC Server Response Time

Test the response time of your OPC server:

```python
import time

opc_server = 'DeltaVEdge'
test_path = 'your/test/path'

start = time.time()
results = system.opc.browse(opc_server, test_path)
elapsed = time.time() - start

print("Browse completed in " + str(elapsed) + " seconds")
print("Items found: " + str(len(results)))

if elapsed > 5:
    print("WARNING: Slow OPC response! Consider reducing scope or increasing timeout.")
```

#### Step 3: Verify Network Connectivity

Check if network issues are causing delays:

1. Ping the OPC server from the Ignition gateway machine
2. Check network latency
3. Verify firewall settings aren't blocking OPC UA traffic

#### Step 4: Monitor Gateway Resources

High CPU or memory usage can cause timeouts:

1. Open Gateway webpage > **Status** > **Performance**
2. Check CPU usage during script execution
3. Check memory usage
4. If resources are constrained, reduce `CHUNK_SIZE` or limit scope

### Performance Optimization Tips

#### 1. Use Specific Tag Filters

```python
# Faster - only searches for CV tags
SEARCH_TAG_NAME = 'CV'

# Slower - imports everything then filters later
SEARCH_TAG_NAME = None
```

#### 2. Target Specific Equipment

```python
# Browse only specific equipment instead of entire system
BASE_OPC_PATH = '.../BRX001/BRX-AI-001/'  # Single instrument
```

#### 3. Schedule During Off-Hours

Run large imports when the OPC server and network are less busy:
- Overnight
- Weekends
- During maintenance windows

#### 4. Use Batch Imports

For multiple bioreactors, run separately:

```python
bioreactors = ['BRX001', 'BRX002', 'BRX003']

for brx in bioreactors:
    print("\nImporting " + brx + "...")
    opc_path = base_template + brx + '/'
    result = import_deltav_tags(opc_server, opc_path, 'default', brx, 'CV')

    # Pause between bioreactors to avoid overwhelming the system
    time.sleep(10)
```

### Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Idle timeout expired` | Script took too long | Use V2.0 script with progress updates |
| `ExecutionException: TimeoutException` | OPC browse timeout | Reduce browsing scope, increase gateway timeout |
| `Connection refused` | OPC server not accessible | Verify OPC connection in Ignition |
| `OutOfMemoryError` | Too many tags at once | Reduce `CHUNK_SIZE` |
| `No browse results` | Invalid OPC path | Verify path in OPC Quick Client |

### Still Having Issues?

If you continue to experience timeouts:

1. **Check the Ignition Gateway logs** (Gateway webpage > **Status** > **Logs**)
2. **Verify OPC server health** - Check DeltaV system status
3. **Test with smaller scope** - Try importing just one folder first
4. **Contact support** - Provide:
   - Ignition version
   - OPC server type and version
   - Number of tags you're trying to import
   - Full error stack trace from logs

### Example: Minimal Test Script

Use this minimal script to test if the timeout is related to scope or configuration:

```python
# Minimal test - import just ONE tag manually
opc_server = 'DeltaVEdge'
opc_path = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/BRX-AI-001/PV/CV'

tag_config = {
    'name': 'TestCV',
    'tagType': 'AtomicTag',
    'dataType': 'Float8',
    'opcServer': opc_server,
    'opcItemPath': opc_path,
    'enabled': True,
    'valueSource': 'opc'
}

try:
    system.tag.configure('[default]Test', [tag_config], 'o')
    print("SUCCESS! Single tag created.")
    print("The timeout is likely due to browsing scope or number of tags.")
    print("Try reducing the BASE_OPC_PATH or importing fewer tags at once.")
except Exception as e:
    print("FAILED! Issue with OPC connection or configuration.")
    print("Error: " + str(e))
```

## Summary

**Key Takeaways:**
1. ✅ Use the V2.0 script with timeout improvements
2. ✅ Start with narrow browsing scope
3. ✅ Reduce chunk size if needed
4. ✅ Import in batches for large structures
5. ✅ Monitor gateway resources
6. ✅ Test OPC connection first

Most timeout issues can be resolved by using the updated V2.0 script and reducing the browsing scope to target specific equipment or areas rather than browsing entire systems at once.
