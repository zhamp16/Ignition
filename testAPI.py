# Test script to explore Sepasoft API methods

print "========== Testing Material API =========="
print ""

# Test 1: Try to load Material Root
try:
    print "Trying to get Material Root..."
    matRootLink = system.mes.getMESObjectLinkByName('MaterialDef', 'Material Root')
    if matRootLink:
        matRoot = system.mes.loadMESObject(matRootLink.getMESObjectUUID())
        print "Material Root loaded successfully"
        print "Type: " + matRoot.getMESObjectTypeName()

        # Get children
        children = matRoot.getChildCollection()
        print "Children count: " + str(len(children))
        print "Children keys (first 5): " + str(children.keys()[:5])

        # Try to get a specific child
        if len(children) > 0:
            firstKey = children.keys()[0]
            firstChild = children[firstKey]
            print ""
            print "First child:"
            print "  Name: " + firstChild.getName()
            print "  Type: " + firstChild.getMESObjectTypeName()
except Exception as e:
    print "Error: " + str(e)
    import traceback
    traceback.print_exc()

print ""
print "========== Testing Material Folder =========="
print ""

# Test 2: Try to load the Golfballs folder
try:
    print "Trying to get Golfballs folder..."
    # Try different path formats
    paths = ['Golfballs', 'Material Root\\Golfballs', 'Material Root/Golfballs']

    for path in paths:
        try:
            print "  Trying path: " + path
            folderLink = system.mes.getMESObjectLinkByName('MaterialDef', path)
            if folderLink:
                folder = system.mes.loadMESObject(folderLink.getMESObjectUUID())
                print "  SUCCESS! Folder loaded"
                print "  Type: " + folder.getMESObjectTypeName()

                # Get children (materials in this folder)
                children = folder.getChildCollection()
                print "  Materials count: " + str(len(children))

                if len(children) > 0:
                    print "  Materials in folder:"
                    for childKey, childMat in children.items():
                        print "    - " + childMat.getName()
                break
        except:
            continue

except Exception as e:
    print "Error: " + str(e)
    import traceback
    traceback.print_exc()

print ""
print "========== Testing Equipment API =========="
print ""

# Test 3: Test equipment paths
try:
    areaPath = 'Acushnet\\Ball Plant 03\\ASB'
    print "Loading area: " + areaPath

    areaLink = system.mes.getMESObjectLinkByEquipmentPath(areaPath)
    areaUUID = areaLink.getMESObjectUUID()
    areaEquipment = system.mes.loadMESObject(areaUUID)

    print "Area loaded successfully"
    print "Area name: " + areaEquipment.getName()

    # Get children
    children = areaEquipment.getChildCollection()
    print "Children count: " + str(len(children))

    # Examine first child
    if len(children) > 0:
        firstKey = children.keys()[0]
        firstChild = children[firstKey]

        print ""
        print "First child details:"
        print "  Key: " + str(firstKey)
        print "  Name: " + firstChild.getName()
        print "  Type: " + firstChild.getMESObjectTypeName()
        print "  UUID: " + str(firstChild.getUUID())

        # Try to get the equipment path
        try:
            print "  Equipment Path (if available): " + str(firstChild.getEquipmentPath())
        except:
            print "  Equipment Path: Not directly available"

        # The path should be: areaPath + '\\' + child name
        childPath = areaPath + '\\' + firstChild.getName()
        print "  Constructed Path: " + childPath

        print ""
        print "All children:"
        for childKey, child in children.items():
            childPath = areaPath + '\\' + child.getName()
            print "  - " + child.getName() + " -> " + childPath

except Exception as e:
    print "Error: " + str(e)
    import traceback
    traceback.print_exc()
