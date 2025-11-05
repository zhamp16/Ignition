"""
Example: Batch Import Multiple DeltaV Bioreactor Tags

This example shows how to import tags from multiple bioreactors
and different tag types in a single script execution.
"""

# Import the main function from the import script
# NOTE: In Ignition, you would either:
# 1. Copy the functions directly into this script, OR
# 2. Save the functions as a project library script and import them

# For this example, we'll assume the functions are available
# If running standalone, uncomment and copy the functions here:
# from import_deltav_opc_tags import import_deltav_tags


def import_multiple_bioreactors():
    """
    Import CV tags from multiple bioreactor units.
    """
    # Configuration
    opc_server = 'DeltaVEdge'
    tag_provider = 'default'
    base_path_template = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/'

    # List of bioreactor units to import
    bioreactors = ['BRX001', 'BRX002', 'BRX003', 'BRX004']

    # Track results
    total_tags_created = 0
    total_folders_created = 0

    print("Starting batch import for multiple bioreactors...")
    print("=" * 80)

    for brx in bioreactors:
        print("\nProcessing " + brx + "...")

        # Build the full OPC path for this bioreactor
        opc_path = base_path_template + brx + '/'

        try:
            # Import CV tags for this bioreactor
            result = import_deltav_tags(
                opc_server=opc_server,
                base_opc_path=opc_path,
                tag_provider=tag_provider,
                root_folder=brx,
                search_tag_name='CV',
                data_type='Float8'
            )

            # Accumulate results
            if result['success']:
                total_tags_created += result['tags_created']
                total_folders_created += result['folders_created']
                print("SUCCESS: " + brx + " - Created " + str(result['tags_created']) + " tags")
            else:
                print("FAILED: " + brx)

        except Exception as e:
            print("ERROR importing " + brx + ": " + str(e))

    # Print summary
    print("\n" + "=" * 80)
    print("BATCH IMPORT COMPLETE")
    print("=" * 80)
    print("Total Tags Created: " + str(total_tags_created))
    print("Total Folders Created: " + str(total_folders_created))
    print("=" * 80)


def import_multiple_tag_types():
    """
    Import different tag types (CV, PV, SP, etc.) for a single bioreactor.
    """
    # Configuration
    opc_server = 'DeltaVEdge'
    tag_provider = 'default'
    bioreactor = 'BRX001'
    base_opc_path = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/' + bioreactor + '/'

    # Tag types to import
    tag_types = [
        {'name': 'CV', 'data_type': 'Float8', 'description': 'Control Values'},
        {'name': 'PV', 'data_type': 'Float8', 'description': 'Process Values'},
        {'name': 'SP', 'data_type': 'Float8', 'description': 'Setpoints'},
        {'name': 'OP', 'data_type': 'Float8', 'description': 'Output Values'},
    ]

    print("Starting import of multiple tag types for " + bioreactor + "...")
    print("=" * 80)

    for tag_type in tag_types:
        print("\nImporting " + tag_type['description'] + " (" + tag_type['name'] + ")...")

        try:
            result = import_deltav_tags(
                opc_server=opc_server,
                base_opc_path=base_opc_path,
                tag_provider=tag_provider,
                root_folder=bioreactor + '_' + tag_type['name'],  # e.g., BRX001_CV
                search_tag_name=tag_type['name'],
                data_type=tag_type['data_type']
            )

            if result['success']:
                print("SUCCESS: Created " + str(result['tags_created']) + " " + tag_type['name'] + " tags")
            else:
                print("FAILED: " + tag_type['name'])

        except Exception as e:
            print("ERROR importing " + tag_type['name'] + ": " + str(e))

    print("\n" + "=" * 80)
    print("TAG TYPE IMPORT COMPLETE")
    print("=" * 80)


def import_with_unified_structure():
    """
    Import all tag types into a single unified folder structure.
    This will preserve the complete hierarchy including the tag type folders.
    """
    # Configuration
    opc_server = 'DeltaVEdge'
    tag_provider = 'default'
    bioreactor = 'BRX001'
    base_opc_path = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/' + bioreactor + '/'

    print("Importing all tags with unified structure for " + bioreactor + "...")
    print("=" * 80)

    try:
        # Import ALL tags (no filter) - this preserves the complete structure
        result = import_deltav_tags(
            opc_server=opc_server,
            base_opc_path=base_opc_path,
            tag_provider=tag_provider,
            root_folder=bioreactor,
            search_tag_name=None,  # No filter - import everything
            data_type='Float8'
        )

        if result['success']:
            print("\nSUCCESS!")
            print("Created " + str(result['tags_created']) + " tags")
            print("Created " + str(result['folders_created']) + " folders")
        else:
            print("\nFAILED")

    except Exception as e:
        print("ERROR: " + str(e))
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)


def import_specific_instruments():
    """
    Import tags only from specific instruments/modules.
    """
    # Configuration
    opc_server = 'DeltaVEdge'
    tag_provider = 'default'
    bioreactor = 'BRX001'

    # Specific instruments to import
    instruments = [
        'BRX-AI-001',  # Analog Input 1
        'BRX-AI-002',  # Analog Input 2
        'BRX-TI-001',  # Temperature Input 1
    ]

    print("Importing tags from specific instruments...")
    print("=" * 80)

    for instrument in instruments:
        print("\nProcessing " + instrument + "...")

        # Build OPC path for this specific instrument
        opc_path = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/' + bioreactor + '/' + instrument + '/'

        try:
            # Import all tags for this instrument
            result = import_deltav_tags(
                opc_server=opc_server,
                base_opc_path=opc_path,
                tag_provider=tag_provider,
                root_folder=bioreactor + '/' + instrument,  # Nested folder structure
                search_tag_name=None,  # Import all tags for this instrument
                data_type='Float8'
            )

            if result['success']:
                print("SUCCESS: " + instrument + " - Created " + str(result['tags_created']) + " tags")
            else:
                print("FAILED: " + instrument)

        except Exception as e:
            print("ERROR importing " + instrument + ": " + str(e))

    print("\n" + "=" * 80)


# ========== MAIN EXECUTION ==========
if __name__ == '__main__' or True:
    # Uncomment the example you want to run:

    # Example 1: Import from multiple bioreactors
    # import_multiple_bioreactors()

    # Example 2: Import multiple tag types for one bioreactor
    # import_multiple_tag_types()

    # Example 3: Import all tags with unified structure
    import_with_unified_structure()

    # Example 4: Import only specific instruments
    # import_specific_instruments()
