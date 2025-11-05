# DeltaV OPC Tag Import Script for Ignition

## Overview

This script automatically imports tags from a DeltaV Edge OPC UA server into Ignition, creating a mirrored folder structure that matches the OPC server hierarchy.

## Features

- **Recursive OPC Browsing**: Automatically traverses the entire OPC server structure
- **Selective Tag Import**: Search for specific tag names (e.g., "CV", "PV", "SP")
- **Mirrored Folder Structure**: Creates the same folder hierarchy in Ignition as exists on the OPC server
- **Configurable**: Easy-to-modify parameters for different use cases
- **Safe**: Checks for existing tags and folders to prevent duplicates
- **Detailed Logging**: Provides comprehensive feedback during execution

## Requirements

- Ignition 8.x or later
- Configured OPC UA connection to DeltaV Edge server
- Appropriate permissions to create tags in the target tag provider

## Installation

1. Copy `import_deltav_opc_tags.py` to your Ignition project
2. Open the Ignition Designer
3. Navigate to the Script Console or create a Gateway Script

## Configuration

Edit the `main()` function in the script to set your parameters:

```python
# OPC UA server connection name as configured in Ignition
OPC_SERVER = 'DeltaVEdge'

# Base OPC UA path (starting point for browsing)
BASE_OPC_PATH = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/'

# Tag provider in Ignition (typically 'default')
TAG_PROVIDER = 'default'

# Root folder name in Ignition tag browser
ROOT_FOLDER = 'BRX001'

# Tag name to search for (e.g., 'CV', 'PV', 'SP', etc.)
# Set to None to import all tags
SEARCH_TAG_NAME = 'CV'

# Data type for created tags
DATA_TYPE = 'Float8'
```

## Usage Examples

### Example 1: Import All CV Tags from BRX001

```python
result = import_deltav_tags(
    opc_server='DeltaVEdge',
    base_opc_path='nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/',
    tag_provider='default',
    root_folder='BRX001',
    search_tag_name='CV',
    data_type='Float8'
)
```

**Result:**
- OPC Path: `/System/.../BRX001/BRX-AI-001/PV/CV`
- Ignition Tag Path: `[default]BRX001/BRX-AI-001/PV/CV`

### Example 2: Import All PV Tags

```python
result = import_deltav_tags(
    opc_server='DeltaVEdge',
    base_opc_path='nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/',
    tag_provider='default',
    root_folder='BRX001_ProcessValues',
    search_tag_name='PV',
    data_type='Float8'
)
```

### Example 3: Import All Tags (No Filter)

```python
result = import_deltav_tags(
    opc_server='DeltaVEdge',
    base_opc_path='nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/',
    tag_provider='default',
    root_folder='BRX001_AllTags',
    search_tag_name=None,  # Import all tags
    data_type='Float8'
)
```

### Example 4: Batch Import Multiple Tag Types

```python
# Import CV, PV, and SP tags into separate folders
tag_types = ['CV', 'PV', 'SP', 'OP']

for tag_type in tag_types:
    print("\n\nImporting " + tag_type + " tags...")
    result = import_deltav_tags(
        opc_server='DeltaVEdge',
        base_opc_path='nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/',
        tag_provider='default',
        root_folder='BRX001_' + tag_type,
        search_tag_name=tag_type,
        data_type='Float8'
    )
    print("Imported " + str(result['tags_created']) + " " + tag_type + " tags")
```

## How It Works

1. **Browse OPC Server**: The script recursively browses the OPC UA server starting from the specified base path
2. **Filter Tags**: Finds all tags matching the search criteria (or all tags if no filter is specified)
3. **Extract Structure**: Determines the relative path from the base path to each found tag
4. **Create Folders**: Creates a mirrored folder structure in Ignition
5. **Create Tags**: Creates OPC tags in Ignition pointing to the OPC server items

## Folder Structure Example

**OPC Server Structure:**
```
/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/
├── BRX-AI-001/
│   └── PV/
│       └── CV
├── BRX-AI-002/
│   └── PV/
│       └── CV
└── BRX-TI-001/
    └── PV/
        └── CV
```

**Resulting Ignition Structure (with ROOT_FOLDER='BRX001'):**
```
[default]BRX001/
├── BRX-AI-001/
│   └── PV/
│       └── CV
├── BRX-AI-002/
│   └── PV/
│       └── CV
└── BRX-TI-001/
    └── PV/
        └── CV
```

## Data Types

Common data types you can use:
- `Float8` - 8-byte floating point (double)
- `Float4` - 4-byte floating point (float)
- `Int4` - 4-byte integer
- `Int8` - 8-byte integer
- `Boolean` - Boolean value
- `String` - Text string

## Troubleshooting

### No tags found
- Verify the OPC server connection is active in Ignition
- Check that the base OPC path is correct
- Use Ignition's OPC Quick Client to verify the path structure
- Ensure the search tag name matches exactly (case-sensitive)

### Tags not created
- Verify you have permissions to create tags in the tag provider
- Check the script console output for error messages
- Ensure the OPC server connection name is correct

### Folder structure incorrect
- The script mirrors the exact structure from the OPC server
- Check the relative path calculation in the logs
- Verify the base OPC path doesn't include extra folders

### Performance issues
- The script includes a max_depth parameter (default: 50) to prevent infinite loops
- For very large tag structures, consider importing in smaller batches
- Monitor Ignition gateway memory during execution

## Advanced Usage

### Custom Data Type Mapping

If you need different data types for different tags, you can modify the script:

```python
def get_data_type_for_tag(tag_name):
    """Return appropriate data type based on tag name"""
    if tag_name in ['CV', 'PV', 'SP']:
        return 'Float8'
    elif tag_name in ['MODE', 'STATUS']:
        return 'Int4'
    elif tag_name in ['ALARM']:
        return 'Boolean'
    else:
        return 'String'

# Then modify the create_opc_tag call:
data_type = get_data_type_for_tag(opc_tag_name)
success = create_opc_tag(tag_provider, current_path, opc_tag_name,
                         opc_server, tag_info['opc_path'], data_type)
```

### Adding Tag Properties

You can extend the tag configuration to include additional properties:

```python
tag_config = {
    'name': tag_name,
    'tagType': 'AtomicTag',
    'dataType': data_type,
    'opcServer': opc_server,
    'opcItemPath': opc_item_path,
    'enabled': True,
    'valueSource': 'opc',
    # Add custom properties
    'engUnit': 'degC',
    'engLow': 0.0,
    'engHigh': 100.0,
    'documentation': 'Imported from DeltaV'
}
```

## Return Value

The `import_deltav_tags()` function returns a dictionary with the following information:

```python
{
    'success': True,           # Whether the operation completed
    'tags_found': 150,         # Number of tags found matching criteria
    'tags_created': 148,       # Number of tags successfully created
    'folders_created': 45      # Number of folders created
}
```

## Support

For issues or questions:
1. Check the Ignition gateway logs
2. Review the script console output
3. Verify OPC server connectivity
4. Consult Ignition documentation for tag configuration

## Version History

- **v1.0** (2025-11-05): Initial release
  - Recursive OPC browsing
  - Folder structure mirroring
  - Configurable tag filtering
  - Detailed logging

## License

This script is provided as-is for use with Ignition SCADA systems.
