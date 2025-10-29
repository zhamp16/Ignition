# Enhanced Material Exploration Script
# This script explores different ways to access materials in Sepasoft

print "=" * 80
print "EXPLORING SEPASOFT MATERIAL API"
print "=" * 80
print ""

# ============================================================================
# Test 1: Try loading a known material directly
# ============================================================================
print "Test 1: Loading a known material directly"
print "-" * 80
try:
    materialName = '2019 ProV1'
    print "Loading material: " + materialName
    matLink = system.mes.getMESObjectLinkByName('MaterialDef', materialName)
    material = system.mes.loadMESObject(matLink.getMESObjectUUID())

    print "SUCCESS! Material loaded:"
    print "  Name: " + material.getName()
    print "  Type: " + material.getMESObjectTypeName()
    print "  UUID: " + str(material.getUUID())

    # Check if it has a parent
    try:
        parents = material.getParentCollection()
        print "  Parent count: " + str(len(parents))
        if len(parents) > 0:
            print "  Parents:"
            for parentKey, parent in parents.items():
                print "    - " + parent.getName() + " (Type: " + parent.getMESObjectTypeName() + ")"
    except Exception as e:
        print "  Could not get parents: " + str(e)

except Exception as e:
    print "FAILED: " + str(e)

print ""

# ============================================================================
# Test 2: Try loading the folder directly
# ============================================================================
print "Test 2: Try loading 'Golfballs' folder directly"
print "-" * 80
try:
    folderName = 'Golfballs'
    print "Loading folder: " + folderName
    folderLink = system.mes.getMESObjectLinkByName('MaterialDef', folderName)
    folder = system.mes.loadMESObject(folderLink.getMESObjectUUID())

    print "SUCCESS! Folder loaded:"
    print "  Name: " + folder.getName()
    print "  Type: " + folder.getMESObjectTypeName()
    print "  UUID: " + str(folder.getUUID())

    # Get children
    children = folder.getChildCollection()
    print "  Children count: " + str(len(children))

    if len(children) > 0:
        print "  Materials in folder:"
        for childKey, child in children.items():
            print "    - " + child.getName()

except Exception as e:
    print "FAILED: " + str(e)

print ""

# ============================================================================
# Test 3: Check available MES object types
# ============================================================================
print "Test 3: What MES object types are available?"
print "-" * 80
try:
    # This might not work, but let's try
    print "Checking system.mes functions..."
    mesFunctions = dir(system.mes)

    # Filter for browse/query/search related functions
    searchFunctions = [f for f in mesFunctions if 'browse' in f.lower() or 'query' in f.lower() or 'search' in f.lower() or 'get' in f.lower()]

    print "Available search/browse functions:"
    for func in searchFunctions:
        print "  - " + func

except Exception as e:
    print "Error: " + str(e)

print ""

# ============================================================================
# Test 4: Try querying materials using SQL/Database approach
# ============================================================================
print "Test 4: Try database query approach"
print "-" * 80
try:
    # Sepasoft stores data in SQL database
    # MaterialDef table might have parent/child relationships

    # Check if we can query the database
    query = "SELECT Name, UUID, ParentUUID FROM MESMaterialDefProperty WHERE Enabled = 1"
    print "Trying SQL query: " + query

    # This might not work in all contexts
    result = system.db.runQuery(query, database="")

    if result:
        print "SUCCESS! Found materials in database:"
        print "Result count: " + str(len(result))

        # Group by parent
        materials = {}
        for row in result:
            parentUUID = str(row['ParentUUID']) if row['ParentUUID'] else 'ROOT'
            if parentUUID not in materials:
                materials[parentUUID] = []
            materials[parentUUID].append(row['Name'])

        print "Materials grouped by parent:"
        for parentUUID, matList in materials.items():
            print "  Parent UUID: " + parentUUID
            for mat in matList[:5]:  # Show first 5
                print "    - " + mat
            if len(matList) > 5:
                print "    ... and " + str(len(matList) - 5) + " more"

except Exception as e:
    print "FAILED: " + str(e)
    import traceback
    traceback.print_exc()

print ""

# ============================================================================
# Test 5: Alternative - Use operation name pattern matching
# ============================================================================
print "Test 5: Alternative approach - List operations and extract materials"
print "-" * 80
print "Since we know operations are named: MaterialName-EquipmentPath"
print "We could list all operations and extract unique material names"
print "However, this requires knowing an equipment path to query against."
print ""

# ============================================================================
# RECOMMENDATION
# ============================================================================
print "=" * 80
print "RECOMMENDATION"
print "=" * 80
print ""
print "Based on the tests above, here are the options:"
print ""
print "Option 1: If 'Golfballs' folder loads successfully (Test 2),"
print "          we can use getChildCollection() to get materials"
print ""
print "Option 2: If database query works (Test 4),"
print "          we can query materials by parent UUID"
print ""
print "Option 3: Manual approach - User provides list of material names"
print "          materials = ['2019 ProV1', '2020 ProV1', '2021 ProV1', ...]"
print ""
print "=" * 80
