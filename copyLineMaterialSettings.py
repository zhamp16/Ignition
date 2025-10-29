materialName = '2019 ProV1'

sourceLinePath = 'Acushnet\Ball Plant 03\OPP\Line 08'
targetLinePath = 'Acushnet\Ball Plant 03\ASB\ASB_02'

# Step 1: Load the material definition
matLink = system.mes.getMESObjectLinkByName('MaterialDef', materialName)

# Step 2: Load the existing operation for the source line
sourceOpName = materialName + '-' + sourceLinePath.replace('\', ':')

# Step 3: Get settings from source
settings = {}
changeoverSettings = {}

# Extract target equipment name from path
targetEquipmentName = targetLinePath.split('\')[-1]
print "Target equipment name: " + targetEquipmentName

try:
    sourceOpDef = system.mes.loadMESObject(sourceOpName, 'OperationsDefinition')

    # Get changeover segment
    sourceChangeoverSegUUID = sourceOpDef.getComplexProperty('SegmentDependency', 'Changeover Dependency').getSegmentRefUUID()
    sourceChangeoverSeg = system.mes.loadMESObject(sourceChangeoverSegUUID)

    # Get production segment
    sourceOpSegUUID = sourceOpDef.getComplexProperty('SegmentDependency', 'Production Dependency').getSegmentRefUUID()
    sourceOpSeg = system.mes.loadMESObject(sourceOpSegUUID)

    # Get TrackProgressBy from Operations Definition
    settings['trackProgressBy'] = sourceOpDef.getTrackProgressBy()

    # ========== CHANGEOVER SETTINGS FROM TRIGGERS ==========
    # Get changeover end trigger (this has duration, mode, and auto)
    endTriggers = sourceChangeoverSeg.getSegmentEndTriggers()
    if len(endTriggers) > 0:
        endTrigger = endTriggers[0]
        changeoverSettings['fixedDuration'] = endTrigger.getFixedDuration()
        changeoverSettings['mode'] = endTrigger.getMode()
        changeoverSettings['timeout'] = endTrigger.getTimeout()
        changeoverSettings['auto'] = endTrigger.getPropertyValue('Auto')

        print "Changeover End Trigger:"
        print "  - Mode: " + str(changeoverSettings['mode'])
        print "  - Fixed Duration: " + str(changeoverSettings['fixedDuration']) + " minute(s)"
        print "  - Auto End: " + str(changeoverSettings['auto'])
        print "  - Timeout: " + str(changeoverSettings['timeout'])

    # Get changeover begin trigger
    beginTriggers = sourceChangeoverSeg.getSegmentBeginTriggers()
    if len(beginTriggers) > 0:
        beginTrigger = beginTriggers[0]
        changeoverSettings['beginMode'] = beginTrigger.getMode()
        changeoverSettings['initialDelay'] = beginTrigger.getInitialDelay()

        print "Changeover Begin Trigger:"
        print "  - Mode: " + str(changeoverSettings['beginMode'])
        print "  - Initial Delay: " + str(changeoverSettings['initialDelay'])

    # ========== CHANGEOVER PRODUCTION SETTINGS ==========
    changeoverCount = sourceChangeoverSeg.getComplexPropertyCount('ProductionSettings')
    if changeoverCount > 0:
        changeoverProdSet = sourceChangeoverSeg.getComplexProperty('ProductionSettings', 0)
        changeoverSettings['changeoverModeUUID'] = changeoverProdSet.getModeRefUUID()
        changeoverSettings['changeoverModeType'] = changeoverProdSet.getModeRefType()

        try:
            changeoverSettings['idleModeUUID'] = changeoverProdSet.getIdleModeRefUUID()
            changeoverSettings['idleModeType'] = changeoverProdSet.getIdleModeRefType()
        except:
            pass

    # ========== IDLE SETTINGS ==========
    prodCount = sourceOpSeg.getComplexPropertyCount('ProductionSettings')
    if prodCount > 0:
        prodSet = sourceOpSeg.getComplexProperty('ProductionSettings', 0)
        try:
            settings['idleModeUUID'] = prodSet.getIdleModeRefUUID()
            settings['idleModeType'] = prodSet.getIdleModeRefType()
        except:
            pass

    # ========== MATERIAL OUT PROPERTIES ==========
    matProp = sourceOpSeg.getComplexProperty('Material', 'Material Out')
    if matProp:
        settings['scheduleRate'] = matProp.getRate()
        settings['units'] = matProp.getUnits()
        settings['ratePeriod'] = matProp.getRatePeriod()

    # ========== PRODUCTION SETTINGS ==========
    prodSettingsList = []
    count = sourceOpSeg.getComplexPropertyCount('ProductionSettings')

    for i in range(count):
        prodSet = sourceOpSeg.getComplexProperty('ProductionSettings', i)

        settingData = {
            'equipmentPath': prodSet.getEquipmentRefProperty(),
            'oeeRate': prodSet.getOEERate(),
            'outfeedUnits': prodSet.getOutfeedUnits(),
            'infeedUnits': prodSet.getInfeedUnits(),
            'infeedScale': prodSet.getInfeedScale(),
            'rejectScale': prodSet.getRejectScale(),
            'packageCount': prodSet.getPackageCount(),
            'modeRefUUID': prodSet.getModeRefUUID(),
            'modeRefType': prodSet.getModeRefType(),
            'idleModeRefUUID': prodSet.getIdleModeRefUUID(),
            'idleModeRefType': prodSet.getIdleModeRefType(),
            'strictTagMode': prodSet.getStrictTagMode() if hasattr(prodSet, 'getStrictTagMode') else False,
        }

        prodSettingsList.append(settingData)

except Exception as e:
    print "Error reading source settings: " + str(e)
    import traceback
    traceback.print_exc()
    raise Exception("Failed to read source settings: " + str(e))

# Get the target equipment MES object for setting infeed/outfeed references
try:
    targetEquipmentLink = system.mes.getMESObjectLinkByEquipmentPath(targetLinePath)
    targetEquipmentUUID = targetEquipmentLink.getMESObjectUUID()
    targetEquipmentType = targetEquipmentLink.getMESObjectTypeName()
except Exception as e:
    print "Could not get target equipment link: " + str(e)
    targetEquipmentUUID = None
    targetEquipmentType = None

# Step 4: Create or get operation for target line
targetOperList = system.mes.oee.createMaterialProcessSegment(matLink, targetLinePath)

# Step 5: Apply settings to target line
for opSeg in targetOperList:
    # Set TrackProgressBy on OperationsDefinition
    if opSeg.getMESObjectTypeName() == 'OperationsDefinition':
        opSeg.setTrackProgressBy(settings['trackProgressBy'])
        print "\nSet TrackProgressBy: " + str(settings['trackProgressBy'])

    # ========== APPLY CHANGEOVER SETTINGS ==========
    if opSeg.getMESObjectTypeName() == 'OperationsSegment':
        if '_CO' in opSeg.getName():
            print "\n========== Applying Changeover Settings =========="
            print "Changeover Segment: " + opSeg.getName()

            # Apply changeover end trigger settings (duration, mode, and auto)
            targetEndTriggers = opSeg.getSegmentEndTriggers()
            if len(targetEndTriggers) > 0 and changeoverSettings:
                targetEndTrigger = targetEndTriggers[0]

                if 'fixedDuration' in changeoverSettings:
                    targetEndTrigger.setFixedDuration(changeoverSettings['fixedDuration'])
                    print "  - Set Fixed Duration: " + str(changeoverSettings['fixedDuration'])

                if 'mode' in changeoverSettings:
                    targetEndTrigger.setMode(changeoverSettings['mode'])
                    print "  - Set Mode: " + str(changeoverSettings['mode'])

                if 'auto' in changeoverSettings:
                    targetEndTrigger.setPropertyValue('Auto', changeoverSettings['auto'])
                    print "  - Set Auto End: " + str(changeoverSettings['auto'])

                if 'timeout' in changeoverSettings:
                    targetEndTrigger.setTimeout(changeoverSettings['timeout'])
                    print "  - Set Timeout: " + str(changeoverSettings['timeout'])

                # Save the trigger back
                opSeg.setPropertyValue('TriggerSegEnd', targetEndTrigger)

            # Apply changeover begin trigger settings
            targetBeginTriggers = opSeg.getSegmentBeginTriggers()
            if len(targetBeginTriggers) > 0 and 'initialDelay' in changeoverSettings:
                targetBeginTrigger = targetBeginTriggers[0]
                targetBeginTrigger.setInitialDelay(changeoverSettings['initialDelay'])
                print "  - Set Initial Delay: " + str(changeoverSettings['initialDelay'])
                opSeg.setPropertyValue('TriggerSegBegin', targetBeginTrigger)

            # Apply ProductionSettings for changeover modes
            changeoverCount = opSeg.getComplexPropertyCount('ProductionSettings')
            if changeoverCount > 0 and changeoverSettings:
                changeoverProdSet = opSeg.getComplexProperty('ProductionSettings', 0)

                if 'changeoverModeUUID' in changeoverSettings:
                    changeoverProdSet.setModeRefUUID(changeoverSettings['changeoverModeUUID'])
                    changeoverProdSet.setModeRefType(changeoverSettings['changeoverModeType'])
                    print "  - Set Changeover Mode"

                if 'idleModeUUID' in changeoverSettings and changeoverSettings['idleModeUUID']:
                    changeoverProdSet.setIdleModeRefUUID(changeoverSettings['idleModeUUID'])
                    changeoverProdSet.setIdleModeRefType(changeoverSettings['idleModeType'])
                    print "  - Set Idle Mode"

                opSeg.setPropertyValue('ProductionSettings', changeoverProdSet)

    # ========== APPLY PRODUCTION SETTINGS ==========
    if opSeg.getMESObjectTypeName() == 'OperationsSegment':
        if '_CO' not in opSeg.getName():
            print "\n========== Applying Production Settings =========="

            # Set Material Out properties
            matProp = opSeg.getComplexProperty('Material', 'Material Out')
            if matProp:
                matProp.setRate(settings['scheduleRate'])
                matProp.setUnits(settings['units'])
                matProp.setRatePeriod(settings['ratePeriod'])
                print "  - Set Material Out properties"

            # Set Production Settings
            targetCount = opSeg.getComplexPropertyCount('ProductionSettings')

            for i in range(targetCount):
                targetProdSet = opSeg.getComplexProperty('ProductionSettings', i)

                if len(prodSettingsList) > 0:
                    sourceSetting = prodSettingsList[0]

                    targetProdSet.setOEERate(sourceSetting['oeeRate'])
                    targetProdSet.setOutfeedUnits(sourceSetting['outfeedUnits'])
                    targetProdSet.setInfeedUnits(sourceSetting['infeedUnits'])
                    targetProdSet.setInfeedScale(sourceSetting['infeedScale'])
                    targetProdSet.setRejectScale(sourceSetting['rejectScale'])
                    targetProdSet.setPackageCount(sourceSetting['packageCount'])

                    # Set mode references
                    if 'modeRefUUID' in sourceSetting and 'modeRefType' in sourceSetting:
                        targetProdSet.setModeRefUUID(sourceSetting['modeRefUUID'])
                        targetProdSet.setModeRefType(sourceSetting['modeRefType'])

                    if 'idleModeRefUUID' in sourceSetting and 'idleModeRefType' in sourceSetting:
                        targetProdSet.setIdleModeRefUUID(sourceSetting['idleModeRefUUID'])
                        targetProdSet.setIdleModeRefType(sourceSetting['idleModeRefType'])

                    # Set infeed/outfeed equipment to TARGET line
                    if targetEquipmentUUID and targetEquipmentType:
                        targetProdSet.setInfeedEquipmentRefUUID(targetEquipmentUUID)
                        targetProdSet.setInfeedEquipmentRefType(targetEquipmentType)
                        targetProdSet.setOutfeedEquipmentRefUUID(targetEquipmentUUID)
                        targetProdSet.setOutfeedEquipmentRefType(targetEquipmentType)
                        print "  - Set infeed/outfeed equipment to: " + targetEquipmentName

                    opSeg.setPropertyValue('ProductionSettings', targetProdSet)

# Step 6: Save all changes
print "\n========== Saving Changes =========="
system.mes.saveMESObjects(targetOperList)

print "\nMaterial '%s' settings copied successfully!" % materialName
print "  Source: %s" % sourceLinePath
print "  Target: %s" % targetLinePath
print "  - Track Progress By: Copied"
print "  - Idle Settings: Copied"
print "  - Changeover Duration: %s minute(s)" % str(changeoverSettings.get('fixedDuration', 'N/A'))
print "  - Changeover Mode: %s" % str(changeoverSettings.get('mode', 'N/A'))
print "  - Auto End Changeover: %s" % str(changeoverSettings.get('auto', 'N/A'))
print "  - Production Settings: Copied"
print "  - Infeed/Outfeed Equipment: Set to " + targetEquipmentName
