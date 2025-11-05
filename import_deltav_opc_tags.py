"""
Ignition Script: Recursively Import DeltaV OPC Tags with Mirrored Folder Structure
Version 2.0 - Timeout Optimized

Description:
    This script recursively browses an OPC UA server starting from a base path,
    searches for specific tag names (e.g., "CV", "PV"), and creates a mirrored
    folder structure in Ignition's tag browser with OPC tags pointing to the
    found items.

    V2.0 Changes:
    - Added timeout handling and retry logic
    - Progress updates to keep connection alive
    - Chunked tag creation to prevent timeouts
    - Better error recovery

Usage:
    1. Update the configuration parameters in the main() function
    2. Run this script from Ignition's Script Console or as a Gateway script

Author: Claude AI
Date: 2025-11-05
"""

import time

def browse_opc_recursive(opc_server, opc_path, search_tag_name=None, max_depth=50, current_depth=0, progress_callback=None):
    """
    Recursively browse OPC server and find tags matching search criteria.

    Args:
        opc_server (str): Name of the OPC connection in Ignition
        opc_path (str): Current OPC path to browse
        search_tag_name (str): Tag name to search for (e.g., "CV", "PV"). If None, returns all tags.
        max_depth (int): Maximum recursion depth to prevent infinite loops
        current_depth (int): Current recursion depth
        progress_callback (function): Optional callback function for progress updates

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
        # Progress update to keep connection alive
        if progress_callback:
            progress_callback("Browsing: " + opc_path)

        # Browse the current OPC path with retry logic
        browse_results = None
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                browse_results = system.opc.browse(opc_server, opc_path)
                break  # Success, exit retry loop
            except Exception as browse_error:
                if attempt < max_retries - 1:
                    print("Browse attempt " + str(attempt + 1) + " failed, retrying in " + str(retry_delay) + "s: " + str(browse_error))
                    time.sleep(retry_delay)
                else:
                    print("Browse failed after " + str(max_retries) + " attempts: " + opc_path)
                    raise browse_error

        if browse_results is None:
            print("Warning: No browse results for path: " + opc_path)
            return found_tags

        # Process each item in the browse results
        item_count = 0
        for result in browse_results:
            item_count += 1

            # Progress update every 10 items
            if item_count % 10 == 0 and progress_callback:
                progress_callback("Browsed " + str(item_count) + " items in " + opc_path)

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
                        current_depth + 1,
                        progress_callback
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


def create_tags_in_chunks(tag_configs, chunk_size=50):
    """
    Create multiple tags in chunks to prevent timeouts.

    Args:
        tag_configs (list): List of tag configuration dictionaries
        chunk_size (int): Number of tags to create at once

    Returns:
        int: Number of successfully created tags
    """
    total_created = 0
    total_tags = len(tag_configs)

    for i in range(0, total_tags, chunk_size):
        chunk = tag_configs[i:i + chunk_size]
        chunk_end = min(i + chunk_size, total_tags)

        print("Creating tags " + str(i + 1) + " to " + str(chunk_end) + " of " + str(total_tags))

        for config in chunk:
            try:
                success = create_opc_tag(
                    config['tag_provider'],
                    config['tag_path'],
                    config['tag_name'],
                    config['opc_server'],
                    config['opc_item_path'],
                    config['data_type']
                )
                if success:
                    total_created += 1
            except Exception as e:
                print("Error creating tag: " + str(e))

        # Small delay between chunks
        if chunk_end < total_tags:
            time.sleep(0.5)

    return total_created


def import_deltav_tags(opc_server, base_opc_path, tag_provider, root_folder, search_tag_name, data_type='Float8', chunk_size=50):
    """
    Main function to import DeltaV OPC tags with mirrored folder structure.

    Args:
        opc_server (str): Name of the OPC UA connection in Ignition
        base_opc_path (str): Base OPC path to start browsing from
        tag_provider (str): Ignition tag provider name (e.g., 'default')
        root_folder (str): Root folder name in Ignition where tags will be created
        search_tag_name (str): Tag name to search for (e.g., 'CV', 'PV')
        data_type (str): Data type for created tags (default: 'Float8')
        chunk_size (int): Number of tags to create at once (default: 50)

    Returns:
        dict: Summary of the import operation
    """
    print("=" * 80)
    print("Starting DeltaV OPC Tag Import (Timeout Optimized)")
    print("=" * 80)
    print("OPC Server: " + opc_server)
    print("Base OPC Path: " + base_opc_path)
    print("Tag Provider: " + tag_provider)
    print("Root Folder: " + root_folder)
    print("Search Tag Name: " + search_tag_name)
    print("Data Type: " + data_type)
    print("Chunk Size: " + str(chunk_size))
    print("=" * 80)

    # Progress callback to keep connection alive
    last_update_time = [time.time()]  # Use list to make it mutable in nested function

    def progress_update(message):
        current_time = time.time()
        if current_time - last_update_time[0] > 5:  # Update every 5 seconds
            print("[PROGRESS] " + message)
            last_update_time[0] = current_time

    # Step 1: Browse OPC server recursively to find matching tags
    print("\nStep 1: Browsing OPC server...")
    print("This may take several minutes for large structures...")

    start_time = time.time()
    found_tags = browse_opc_recursive(opc_server, base_opc_path, search_tag_name, progress_callback=progress_update)
    browse_time = time.time() - start_time

    print("Found " + str(len(found_tags)) + " matching tags in " + str(int(browse_time)) + " seconds")

    if len(found_tags) == 0:
        print("No tags found matching criteria. Exiting.")
        return {'success': False, 'tags_created': 0, 'folders_created': 0}

    # Step 2: Create root folder
    print("\nStep 2: Creating root folder structure...")
    root_path = create_folder_structure(tag_provider, '', root_folder)
    folders_created = 1

    # Step 3: Build tag configurations and create folder structure
    print("\nStep 3: Analyzing folder structure and preparing tags...")
    tag_configs = []
    folder_cache = set()  # Track created folders to avoid duplicates

    for idx, tag_info in enumerate(found_tags):
        if (idx + 1) % 100 == 0:
            print("Processed " + str(idx + 1) + " / " + str(len(found_tags)) + " tags")

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
                folder_key = current_path + '/' + folder_name
                if folder_key not in folder_cache:
                    current_path = create_folder_structure(tag_provider, current_path, folder_name)
                    folder_cache.add(folder_key)
                    folders_created += 1
                else:
                    # Folder already created, just update path
                    if current_path.endswith('/'):
                        current_path = current_path + folder_name
                    else:
                        current_path = current_path + '/' + folder_name

            # Add tag configuration to list
            tag_configs.append({
                'tag_provider': tag_provider,
                'tag_path': current_path,
                'tag_name': opc_tag_name,
                'opc_server': opc_server,
                'opc_item_path': tag_info['opc_path'],
                'data_type': data_type
            })

        except Exception as e:
            print("Error processing tag '" + tag_info['opc_path'] + "': " + str(e))
            import traceback
            traceback.print_exc()

    # Step 4: Create tags in chunks
    print("\nStep 4: Creating " + str(len(tag_configs)) + " tags in chunks of " + str(chunk_size) + "...")
    tags_created = create_tags_in_chunks(tag_configs, chunk_size)

    # Print summary
    print("\n" + "=" * 80)
    print("Import Complete!")
    print("=" * 80)
    print("Tags Created: " + str(tags_created) + " / " + str(len(found_tags)))
    print("Folders Created: " + str(folders_created))
    print("Total Time: " + str(int(time.time() - start_time)) + " seconds")
    print("=" * 80)

    return {
        'success': True,
        'tags_found': len(found_tags),
        'tags_created': tags_created,
        'folders_created': folders_created,
        'browse_time_seconds': int(browse_time)
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

    # Number of tags to create at once (smaller = slower but more reliable)
    CHUNK_SIZE = 50

    # ========== END CONFIGURATION ==========

    # Execute the import
    result = import_deltav_tags(
        OPC_SERVER,
        BASE_OPC_PATH,
        TAG_PROVIDER,
        ROOT_FOLDER,
        SEARCH_TAG_NAME,
        DATA_TYPE,
        CHUNK_SIZE
    )

    return result


# ========== EXECUTION ==========
# Run the main function
if __name__ == '__main__' or True:  # The 'or True' ensures it runs in Ignition Script Console
    main()
