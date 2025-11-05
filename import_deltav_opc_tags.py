"""
Ignition Script: Recursively Import DeltaV OPC Tags with Mirrored Folder Structure

Description:
    This script recursively browses an OPC UA server starting from a base path,
    searches for specific tag names (e.g., "CV", "PV"), and creates a mirrored
    folder structure in Ignition's tag browser with OPC tags pointing to the
    found items.

Usage:
    1. Update the configuration parameters in the main() function
    2. Run this script from Ignition's Script Console or as a Gateway script

Author: Claude AI
Date: 2025-11-05
"""

def browse_opc_recursive(opc_server, opc_path, search_tag_name=None, max_depth=50, current_depth=0):
    """
    Recursively browse OPC server and find tags matching search criteria.

    Args:
        opc_server (str): Name of the OPC connection in Ignition
        opc_path (str): Current OPC path to browse
        search_tag_name (str): Tag name to search for (e.g., "CV", "PV"). If None, returns all tags.
        max_depth (int): Maximum recursion depth to prevent infinite loops
        current_depth (int): Current recursion depth

    Returns:
        list: List of dictionaries containing tag information
              Format: [{'opc_path': 'full/path/to/tag', 'relative_path': 'relative/path', 'tag_name': 'CV'}]
    """
    found_tags = []

    # Safety check for recursion depth
    if current_depth >= max_depth:
        print("Warning: Maximum recursion depth reached at path: " + opc_path)
        return found_tags

    try:
        # Browse the current OPC path
        browse_results = system.opc.browse(opc_server, opc_path)

        if browse_results is None:
            print("Warning: No browse results for path: " + opc_path)
            return found_tags

        # Process each item in the browse results
        for result in browse_results:
            item_name = result.getDisplayName()
            item_type = result.getNodeClass()

            # Build the full path for this item
            if opc_path.endswith('/'):
                full_path = opc_path + item_name
            else:
                full_path = opc_path + '/' + item_name

            # Check if this is a folder/object (NodeClass = 1 for Object)
            # or a variable (NodeClass = 2 for Variable)
            if item_type.getValue() == 1:  # Object/Folder
                # Recursively browse into this folder
                found_tags.extend(
                    browse_opc_recursive(
                        opc_server,
                        full_path,
                        search_tag_name,
                        max_depth,
                        current_depth + 1
                    )
                )
            elif item_type.getValue() == 2:  # Variable/Tag
                # Check if this tag matches our search criteria
                if search_tag_name is None or item_name == search_tag_name:
                    found_tags.append({
                        'opc_path': full_path,
                        'tag_name': item_name,
                        'item_type': item_type.getValue()
                    })

    except Exception as e:
        print("Error browsing OPC path '" + opc_path + "': " + str(e))
        import traceback
        traceback.print_exc()

    return found_tags


def get_relative_path(full_opc_path, base_opc_path):
    """
    Extract the relative path from a full OPC path given a base path.

    Args:
        full_opc_path (str): Full OPC path to the tag
        base_opc_path (str): Base OPC path to remove

    Returns:
        str: Relative path from base to the tag
    """
    # Normalize paths by removing trailing slashes
    base = base_opc_path.rstrip('/')
    full = full_opc_path.rstrip('/')

    if full.startswith(base):
        relative = full[len(base):]
        # Remove leading slash
        relative = relative.lstrip('/')
        return relative
    else:
        # If the full path doesn't start with base, return the full path
        return full


def create_folder_structure(tag_provider, parent_path, folder_name):
    """
    Create a folder in Ignition's tag browser if it doesn't exist.

    Args:
        tag_provider (str): Name of the tag provider
        parent_path (str): Parent path where to create the folder
        folder_name (str): Name of the folder to create

    Returns:
        str: Full path to the created/existing folder
    """
    # Build full folder path
    if parent_path:
        if parent_path.endswith('/'):
            folder_path = parent_path + folder_name
        else:
            folder_path = parent_path + '/' + folder_name
    else:
        folder_path = folder_name

    # Prepend provider if specified
    if tag_provider:
        full_path = '[' + tag_provider + ']' + folder_path
    else:
        full_path = folder_path

    # Check if folder already exists
    if system.tag.exists(full_path):
        return folder_path

    # Create folder configuration
    folder_config = {
        'name': folder_name,
        'tagType': 'Folder'
    }

    # Determine the parent path for configuration
    config_parent = '[' + tag_provider + ']' + parent_path if tag_provider else parent_path

    try:
        # Create the folder
        system.tag.configure(config_parent, [folder_config], 'o')
        print("Created folder: " + full_path)
    except Exception as e:
        print("Error creating folder '" + full_path + "': " + str(e))

    return folder_path


def create_opc_tag(tag_provider, tag_path, tag_name, opc_server, opc_item_path, data_type='Float8'):
    """
    Create an OPC tag in Ignition.

    Args:
        tag_provider (str): Name of the tag provider
        tag_path (str): Parent path where to create the tag
        tag_name (str): Name of the tag
        opc_server (str): OPC server connection name
        opc_item_path (str): Full OPC item path
        data_type (str): Data type for the tag (default: Float8)

    Returns:
        bool: True if successful, False otherwise
    """
    # Build full tag path
    if tag_provider:
        if tag_path:
            parent_path = '[' + tag_provider + ']' + tag_path
            full_tag_path = '[' + tag_provider + ']' + tag_path + '/' + tag_name
        else:
            parent_path = '[' + tag_provider + ']'
            full_tag_path = '[' + tag_provider + ']' + tag_name
    else:
        parent_path = tag_path
        full_tag_path = tag_path + '/' + tag_name if tag_path else tag_name

    # Check if tag already exists
    if system.tag.exists(full_tag_path):
        print("Tag already exists, skipping: " + full_tag_path)
        return True

    # Create OPC tag configuration
    tag_config = {
        'name': tag_name,
        'tagType': 'AtomicTag',
        'dataType': data_type,
        'opcServer': opc_server,
        'opcItemPath': opc_item_path,
        'enabled': True,
        'valueSource': 'opc'
    }

    try:
        # Create the tag
        system.tag.configure(parent_path, [tag_config], 'o')
        print("Created OPC tag: " + full_tag_path + " -> " + opc_item_path)
        return True
    except Exception as e:
        print("Error creating tag '" + full_tag_path + "': " + str(e))
        import traceback
        traceback.print_exc()
        return False


def import_deltav_tags(opc_server, base_opc_path, tag_provider, root_folder, search_tag_name, data_type='Float8'):
    """
    Main function to import DeltaV OPC tags with mirrored folder structure.

    Args:
        opc_server (str): Name of the OPC UA connection in Ignition
        base_opc_path (str): Base OPC path to start browsing from
        tag_provider (str): Ignition tag provider name (e.g., 'default')
        root_folder (str): Root folder name in Ignition where tags will be created
        search_tag_name (str): Tag name to search for (e.g., 'CV', 'PV')
        data_type (str): Data type for created tags (default: 'Float8')

    Returns:
        dict: Summary of the import operation
    """
    print("=" * 80)
    print("Starting DeltaV OPC Tag Import")
    print("=" * 80)
    print("OPC Server: " + opc_server)
    print("Base OPC Path: " + base_opc_path)
    print("Tag Provider: " + tag_provider)
    print("Root Folder: " + root_folder)
    print("Search Tag Name: " + search_tag_name)
    print("Data Type: " + data_type)
    print("=" * 80)

    # Step 1: Browse OPC server recursively to find matching tags
    print("\nStep 1: Browsing OPC server...")
    found_tags = browse_opc_recursive(opc_server, base_opc_path, search_tag_name)
    print("Found " + str(len(found_tags)) + " matching tags")

    if len(found_tags) == 0:
        print("No tags found matching criteria. Exiting.")
        return {'success': False, 'tags_created': 0, 'folders_created': 0}

    # Step 2: Create root folder
    print("\nStep 2: Creating root folder structure...")
    root_path = create_folder_structure(tag_provider, '', root_folder)
    folders_created = 1
    tags_created = 0

    # Step 3: Process each found tag
    print("\nStep 3: Creating tags and folder structure...")
    for tag_info in found_tags:
        try:
            # Get relative path from base OPC path
            relative_path = get_relative_path(tag_info['opc_path'], base_opc_path)

            # Split relative path into folders and tag name
            path_parts = relative_path.split('/')

            # The last part should be the tag name
            opc_tag_name = path_parts[-1]

            # Everything except the last part is the folder structure
            folder_structure = path_parts[:-1]

            # Create nested folder structure
            current_path = root_path
            for folder_name in folder_structure:
                current_path = create_folder_structure(tag_provider, current_path, folder_name)
                folders_created += 1

            # Create the OPC tag
            success = create_opc_tag(
                tag_provider,
                current_path,
                opc_tag_name,
                opc_server,
                tag_info['opc_path'],
                data_type
            )

            if success:
                tags_created += 1

        except Exception as e:
            print("Error processing tag '" + tag_info['opc_path'] + "': " + str(e))
            import traceback
            traceback.print_exc()

    # Print summary
    print("\n" + "=" * 80)
    print("Import Complete!")
    print("=" * 80)
    print("Tags Created: " + str(tags_created) + " / " + str(len(found_tags)))
    print("Folders Created: " + str(folders_created))
    print("=" * 80)

    return {
        'success': True,
        'tags_found': len(found_tags),
        'tags_created': tags_created,
        'folders_created': folders_created
    }


def main():
    """
    Main execution function - Configure your parameters here.
    """
    # ========== CONFIGURATION PARAMETERS ==========

    # OPC UA server connection name as configured in Ignition
    OPC_SERVER = 'DeltaVEdge'

    # Base OPC UA path (starting point for browsing)
    # Example: 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/'
    BASE_OPC_PATH = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001/'

    # Tag provider in Ignition (typically 'default')
    TAG_PROVIDER = 'default'

    # Root folder name in Ignition tag browser
    ROOT_FOLDER = 'BRX001'

    # Tag name to search for (e.g., 'CV', 'PV', 'SP', etc.)
    # Set to None to import all tags
    SEARCH_TAG_NAME = 'CV'

    # Data type for created tags
    # Common types: 'Float8', 'Float4', 'Int4', 'Int8', 'Boolean', 'String'
    DATA_TYPE = 'Float8'

    # ========== END CONFIGURATION ==========

    # Execute the import
    result = import_deltav_tags(
        OPC_SERVER,
        BASE_OPC_PATH,
        TAG_PROVIDER,
        ROOT_FOLDER,
        SEARCH_TAG_NAME,
        DATA_TYPE
    )

    return result


# ========== EXECUTION ==========
# Run the main function
if __name__ == '__main__' or True:  # The 'or True' ensures it runs in Ignition Script Console
    main()
