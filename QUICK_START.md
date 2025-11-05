# Quick Start Guide - DeltaV OPC Tag Import

## Step 1: Configure Your OPC Connection

Make sure your OPC UA connection is configured in Ignition:
1. Open Gateway webpage
2. Go to **Config** > **OPC UA** > **Connections**
3. Note the exact connection name (e.g., "DeltaV Edge OPC UA")

## Step 2: Find Your Base Node ID

Use the script console to find your starting node:

```python
# Test script - paste in Ignition Script Console
server = 'DeltaV Edge OPC UA'  # Your OPC connection name
nodeId = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001'

items = system.opc.browseServer(server, nodeId)
print 'Found ' + str(len(items)) + ' items:'
for item in items:
    print '  - ' + item.getDisplayName()
```

## Step 3: Configure the Import Script

Open `import_deltav_opc_tags.py` and update these settings in the `main()` function:

```python
# Your OPC connection name (from Step 1)
OPC_SERVER = 'DeltaV Edge OPC UA'

# Your base node ID (from Step 2)
BASE_NODE_ID = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001'

# Root folder in Ignition where tags will be created
ROOT_FOLDER = 'BRX001'

# Tag name to search for (e.g., 'CV', 'PV', 'SP')
SEARCH_TAG_NAME = 'CV'

# IMPORTANT: Start with dry run to test
DRY_RUN = True  # This will only print paths, not create tags
```

## Step 4: Test with Dry Run

1. Copy the entire `import_deltav_opc_tags.py` script
2. Paste into Ignition Script Console
3. Click **Run Script**
4. Review the output - it will show all tag paths that would be created

Expected output:
```
================================================================================
DeltaV OPC Tag Import - Iterative Browsing
================================================================================
OPC Server: DeltaV Edge OPC UA
Base Node: nsu=http://inmation.com/UA/;s=/.../BRX001
Search Tag Name: CV
DRY RUN: True
================================================================================

Step 1: Browsing OPC server...
Starting iterative OPC browsing...
[Iteration 10] Queue size: 45, Tags found: 3
[Iteration 20] Queue size: 38, Tags found: 8
...

Browse complete!
Iterations: 152
Total items browsed: 1247
Tags found matching criteria: 145
================================================================================

*** DRY RUN MODE - Only printing paths, not creating tags ***

================================================================================
TAG PATHS THAT WOULD BE CREATED:
================================================================================

--- Folder: BRX001/BRX-AI-001/PV ---
  [1] [default]BRX001/BRX-AI-001/PV/CV
      OPC: nsu=http://inmation.com/UA/;i=12345

--- Folder: BRX001/BRX-AI-002/PV ---
  [2] [default]BRX001/BRX-AI-002/PV/CV
      OPC: nsu=http://inmation.com/UA/;i=12346

...

================================================================================
SUMMARY:
  Folders: 48
  Tags: 145
================================================================================
```

## Step 5: Review the Results

Check the printed output:
- ✅ Are the tag paths correct?
- ✅ Are they in the right folder structure?
- ✅ Is the count reasonable?

## Step 6: Create the Tags (Live Run)

If everything looks good:

1. In the script, change `DRY_RUN = False`
2. Run the script again
3. Watch the output as tags are created

Expected output:
```
*** LIVE MODE - Creating tags in Ignition ***

================================================================================
CREATING TAGS IN IGNITION
================================================================================

Creating root folder: BRX001
Created folder: [default]BRX001

Analyzing folder structure...
Created folder: [default]BRX001/BRX-AI-001
Created folder: [default]BRX001/BRX-AI-001/PV
Created OPC tag: [default]BRX001/BRX-AI-001/PV/CV
Created folder: [default]BRX001/BRX-AI-002
Created folder: [default]BRX001/BRX-AI-002/PV
Created OPC tag: [default]BRX001/BRX-AI-002/PV/CV
Processing tag 50 / 145
...

================================================================================
TAG CREATION COMPLETE
================================================================================
Tags Created: 145 / 145
Folders Created: 48
================================================================================
```

## Step 7: Verify in Designer

1. Open Ignition Designer
2. Go to **Tag Browser**
3. Expand your root folder (e.g., `[default]BRX001`)
4. Verify the folder structure and tags match your OPC server

## Common Issues

### "Connection refused" or "Cannot browse"
- Check OPC connection is active in Gateway
- Verify connection name is exact (case-sensitive)
- Test with OPC Quick Client first

### "No tags found matching criteria"
- Check `SEARCH_TAG_NAME` matches exactly (case-sensitive)
- Try `SEARCH_TAG_NAME = None` to import all tags
- Verify base node ID is correct

### Tags created in wrong location
- Check `ROOT_FOLDER` setting
- Check `TAG_PROVIDER` is correct (usually 'default')

## Tips for Success

### 1. Start Small
Test with one bioreactor before importing multiple:
```python
BASE_NODE_ID = '.../BRX001'  # Just one bioreactor
```

### 2. Import Different Tag Types
Run multiple times for different tag types:
```python
# First run
SEARCH_TAG_NAME = 'CV'
ROOT_FOLDER = 'BRX001_CV'

# Second run
SEARCH_TAG_NAME = 'PV'
ROOT_FOLDER = 'BRX001_PV'
```

### 3. Monitor Performance
Watch the iteration count and queue size:
- High queue size = lots of folders to browse
- Many iterations = deep hierarchy
- Both are fine, the script handles them without timing out

### 4. Adjust MAX_ITERATIONS if Needed
For very large structures:
```python
MAX_ITERATIONS = 5000  # Default is 2000
```

## Example: Import All CV Tags from Multiple Bioreactors

```python
# List of bioreactors to import
bioreactors = ['BRX001', 'BRX002', 'BRX003']

for brx in bioreactors:
    print("\n\n========================================")
    print("Processing: " + brx)
    print("========================================\n")

    # Update configuration
    OPC_SERVER = 'DeltaV Edge OPC UA'
    BASE_NODE_ID = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/' + brx
    TAG_PROVIDER = 'default'
    ROOT_FOLDER = brx
    SEARCH_TAG_NAME = 'CV'
    DATA_TYPE = 'Float8'
    CHUNK_SIZE = 50
    MAX_ITERATIONS = 2000
    DRY_RUN = False  # Create tags

    # Run import (copy the import_deltav_tags function here)
    result = import_deltav_tags(
        OPC_SERVER,
        BASE_NODE_ID,
        TAG_PROVIDER,
        ROOT_FOLDER,
        SEARCH_TAG_NAME,
        DATA_TYPE,
        CHUNK_SIZE
    )

    print("\nCompleted " + brx + ": " + str(result['tags_created']) + " tags created")
```

## Next Steps

After successful import:
- Set up alarms on imported tags
- Create HMI displays using the tags
- Set up tag history if needed
- Create derived tags or expressions

## Support

If you encounter issues:
1. Check the script console output for error messages
2. Review `TIMEOUT_TROUBLESHOOTING.md` for common problems
3. Test OPC connection with OPC Quick Client
4. Verify node IDs using the test script in Step 2
