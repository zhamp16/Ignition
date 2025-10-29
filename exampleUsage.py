"""
Example Usage Script for Material Settings Library

This script demonstrates how to copy material settings from one source line
to all lines in a different area for all materials in a folder.

Use Case:
- Copy settings from Line 08 in OPP area to all lines in ASB area
- Apply to all materials in the "Golfballs" folder
"""

# Import the library functions
from materialSettingsLibrary import copyLineMaterialSettings, getMaterialsInFolder, getLinesInArea


# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Source line that has the correct settings
SOURCE_LINE = 'Acushnet\\Ball Plant 03\\OPP\\Line 08'

# Area containing target lines
TARGET_AREA = 'Acushnet\\Ball Plant 03\\ASB'

# Material folder to process
MATERIAL_FOLDER = 'Golfballs'


# ==============================================================================
# EXECUTION
# ==============================================================================

print "=" * 80
print "MATERIAL SETTINGS COPY UTILITY"
print "=" * 80
print ""

# Step 1: Get all materials in the folder
print "Step 1: Getting materials from folder '%s'..." % MATERIAL_FOLDER
materials = getMaterialsInFolder(MATERIAL_FOLDER)
print "  Found: %s" % ', '.join(materials)
print ""

# Step 2: Get all lines in the target area
print "Step 2: Getting lines from area '%s'..." % TARGET_AREA
targetLines = getLinesInArea(TARGET_AREA)
print "  Found: %s" % ', '.join([line.split('\\')[-1] for line in targetLines])
print ""

# Step 3: Copy settings
print "Step 3: Copying settings from source to all target lines..."
print ""

results = copyLineMaterialSettings(SOURCE_LINE, targetLines, materials)

# Done!
print ""
print "=" * 80
print "COMPLETE"
print "=" * 80
print ""


# ==============================================================================
# ALTERNATIVE USAGE EXAMPLES
# ==============================================================================

# Example 1: Copy specific materials to specific lines
"""
sourcePath = 'Acushnet\\\\Ball Plant 03\\\\OPP\\\\Line 08'
targetPaths = [
    'Acushnet\\\\Ball Plant 03\\\\ASB\\\\ASB_01',
    'Acushnet\\\\Ball Plant 03\\\\ASB\\\\ASB_02'
]
materialNames = ['2019 ProV1', '2020 ProV1']

result = copyLineMaterialSettings(sourcePath, targetPaths, materialNames)
"""

# Example 2: Copy single material to multiple lines
"""
sourcePath = 'Acushnet\\\\Ball Plant 03\\\\OPP\\\\Line 08'
targetLines = getLinesInArea('Acushnet\\\\Ball Plant 03\\\\ASB')
materialNames = ['2019 ProV1']

result = copyLineMaterialSettings(sourcePath, targetLines, materialNames)
"""

# Example 3: Copy multiple materials from different folders
"""
sourcePath = 'Acushnet\\\\Ball Plant 03\\\\OPP\\\\Line 08'
targetPaths = ['Acushnet\\\\Ball Plant 03\\\\ASB\\\\ASB_01']

# Combine materials from multiple folders
materials = []
materials.extend(getMaterialsInFolder('Golfballs'))
materials.extend(getMaterialsInFolder('OtherProducts'))

result = copyLineMaterialSettings(sourcePath, targetPaths, materials)
"""
