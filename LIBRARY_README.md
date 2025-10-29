# Material Settings Copy Library

A reusable library for copying Sepasoft MES material operation settings between lines.

## Overview

This library provides functions to efficiently copy material settings from a source line to multiple target lines, making it easy to standardize configurations across your production environment.

## Features

- **Bulk Operations**: Copy settings for multiple materials to multiple lines in a single operation
- **Helper Functions**: Easily retrieve materials from folders and lines from equipment areas
- **Comprehensive Settings**: Copies all operation settings including:
  - Track Progress By
  - Changeover duration, mode, and auto-end settings
  - Changeover and production modes
  - Material out properties (rate, units, rate period)
  - Production settings (OEE rate, infeed/outfeed, scales, package count)
  - Infeed/outfeed equipment references
- **Error Handling**: Detailed error reporting and success tracking
- **Progress Reporting**: Real-time feedback during copy operations

## Files

- **`materialSettingsLibrary.py`** - Main library with all functions
- **`exampleUsage.py`** - Example script demonstrating usage
- **`copyLineMaterialSettings.py`** - Original single-use script (kept for reference)

## Functions

### `copyLineMaterialSettings(sourcePath, targetPaths, materialNames)`

Main function to copy material settings from one source line to multiple target lines.

**Parameters:**
- `sourcePath` (str): Equipment path of the source line
- `targetPaths` (list): List of target line equipment paths
- `materialNames` (list): List of material names to process

**Returns:**
- `dict`: Summary with success/failure counts and details

**Example:**
```python
from materialSettingsLibrary import copyLineMaterialSettings

sourcePath = 'Acushnet\\Ball Plant 03\\OPP\\Line 08'
targetPaths = [
    'Acushnet\\Ball Plant 03\\ASB\\ASB_01',
    'Acushnet\\Ball Plant 03\\ASB\\ASB_02'
]
materialNames = ['2019 ProV1', '2020 ProV1']

result = copyLineMaterialSettings(sourcePath, targetPaths, materialNames)
```

### `getMaterialsInFolder(folderPath)`

Get all material names in a given material folder.

**Parameters:**
- `folderPath` (str): Path to the material folder

**Returns:**
- `list`: List of material names

**Example:**
```python
from materialSettingsLibrary import getMaterialsInFolder

materials = getMaterialsInFolder('Golfballs')
print materials  # ['2019 ProV1', '2020 ProV1', ...]
```

### `getLinesInArea(areaPath)`

Get all line equipment paths within a given area.

**Parameters:**
- `areaPath` (str): Equipment path to the area

**Returns:**
- `list`: List of line equipment paths

**Example:**
```python
from materialSettingsLibrary import getLinesInArea

lines = getLinesInArea('Acushnet\\Ball Plant 03\\ASB')
print lines  # ['Acushnet\\Ball Plant 03\\ASB\\ASB_01', ...]
```

## Common Use Cases

### Copy All Materials in a Folder to All Lines in an Area

```python
from materialSettingsLibrary import copyLineMaterialSettings, getMaterialsInFolder, getLinesInArea

# Source line with correct settings
sourceLine = 'Acushnet\\Ball Plant 03\\OPP\\Line 08'

# Get all materials from folder
materials = getMaterialsInFolder('Golfballs')

# Get all target lines from area
targetLines = getLinesInArea('Acushnet\\Ball Plant 03\\ASB')

# Copy settings
result = copyLineMaterialSettings(sourceLine, targetLines, materials)
```

### Copy Specific Materials to Specific Lines

```python
from materialSettingsLibrary import copyLineMaterialSettings

sourceLine = 'Acushnet\\Ball Plant 03\\OPP\\Line 08'
targetLines = [
    'Acushnet\\Ball Plant 03\\ASB\\ASB_01',
    'Acushnet\\Ball Plant 03\\ASB\\ASB_02'
]
materials = ['2019 ProV1', '2020 ProV1']

result = copyLineMaterialSettings(sourceLine, targetLines, materials)
```

### Copy Materials from Multiple Folders

```python
from materialSettingsLibrary import copyLineMaterialSettings, getMaterialsInFolder

sourceLine = 'Acushnet\\Ball Plant 03\\OPP\\Line 08'
targetLines = ['Acushnet\\Ball Plant 03\\ASB\\ASB_01']

# Combine materials from multiple folders
materials = []
materials.extend(getMaterialsInFolder('Golfballs'))
materials.extend(getMaterialsInFolder('OtherProducts'))

result = copyLineMaterialSettings(sourceLine, targetLines, materials)
```

## Path Format

Equipment paths should use double backslashes as separators:
- Correct: `'Acushnet\\Ball Plant 03\\OPP\\Line 08'`
- Incorrect: `'Acushnet\Ball Plant 03\OPP\Line 08'` (single backslash is an escape character)

## Error Handling

The library includes comprehensive error handling:
- Failed operations are logged with detailed error messages
- The results dictionary includes all failures with error details
- Operations continue even if individual materials/lines fail
- Full stack traces are printed for debugging

## Return Value Structure

```python
{
    'successful': [
        {'material': '2019 ProV1', 'targetPath': 'Acushnet\\Ball Plant 03\\ASB\\ASB_01'},
        ...
    ],
    'failed': [
        {'material': '2020 ProV1', 'targetPath': 'Acushnet\\Ball Plant 03\\ASB\\ASB_02', 'error': 'Error message'},
        ...
    ],
    'totalProcessed': 10,
    'totalSuccess': 8,
    'totalFailed': 2
}
```

## Requirements

- Sepasoft MES module installed
- Ignition Gateway with proper permissions
- Access to `system.mes` functions

## Technical Details

### Settings Copied

1. **Operations Definition Settings**
   - Track Progress By

2. **Changeover Segment Settings**
   - End trigger: Mode, Fixed Duration, Auto End, Timeout
   - Begin trigger: Mode, Initial Delay
   - Production settings: Changeover mode, Idle mode

3. **Production Segment Settings**
   - Material Out: Rate, Units, Rate Period
   - Production Settings: OEE Rate, Infeed/Outfeed Units and Scales, Reject Scale, Package Count
   - Mode references: Production mode, Idle mode
   - Equipment references: Infeed and Outfeed equipment (set to target line)

### Auto End Property Access

The "Auto End" property on triggers is accessed via the `getChildProperties()` method, not direct getter/setter methods. This is because it's a nested property within the trigger complex property.

## Troubleshooting

**Material not found:**
- Verify the material name is correct and exists in Sepasoft
- Check that the material folder path is correct

**Line not found:**
- Verify the equipment path format (use double backslashes)
- Ensure the equipment exists in Sepasoft hierarchy

**Settings not copying:**
- Check that the source line has an existing operation for the material
- Verify proper permissions to modify MES objects

## Author

Generated by Claude Code

## Date

2025-10-29
