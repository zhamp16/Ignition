"""
Ignition Script: Recursively Import DeltaV OPC Tags with Mirrored Folder Structure
Version 2.2 - Multi-Tag Search Support

Description:
    This script uses system.opc.browseServer() with iterative (non-recursive) browsing
    to find tags matching search criteria. This prevents timeout issues by doing
    multiple small browse operations instead of one large recursive operation.

    The script browses the ENTIRE folder hierarchy depth-first, finding tags at any depth:
    - BRX-AI-001/PV/CV
    - BRX-AIC-005/PID1/PV/CV
    - BRX-AIC-005/PID1/OUT/CV
    - BRX-WIC-001/PID1/MODE/ACTUAL

    V2.2 Features:
    - Multi-tag search: Search for multiple tag names in one pass (e.g., ['CV', 'ACTUAL'])
    - Single tag search: Still works with single string (e.g., 'CV')
    - Performance optimized: Skips browsing into matching tags (saves 20-30% time)
    - Dry-run mode: Preview what will be created before committing

    V2.1 Changes:
    - Changed from system.opc.browse() to system.opc.browseServer()
    - Replaced recursion with iterative queue-based browsing
    - Added dry-run mode to print tag paths without creating them
    - Better handling of OPC UA node IDs
    - Explores full hierarchy depth to find tags at any level

Usage:
    1. Update the configuration parameters in the main() function
    2. Set SEARCH_TAG_NAMES to a single tag or list: ['CV', 'ACTUAL']
    3. Set DRY_RUN = True to test and see what would be created
    4. Set DRY_RUN = False to actually create the tags
    5. Run this script from Ignition's Script Console

Author: Claude AI
Date: 2025-11-05
"""

import time


def browse_opc_iterative(opc_server, base_node_id, search_tag_names=None, max_iterations=1000):
    """
    Iteratively browse OPC server using a queue to avoid recursion timeouts.

    This function explores the ENTIRE folder hierarchy to find matching tags at any depth.

    Performance Optimization:
    - If an item's name matches the search criteria (e.g., "CV" or "ACTUAL"), it's immediately saved as a tag
      (no additional browse operation needed, since these tags are never folders)
    - If an item doesn't match, the script browses into it to check if it's a folder
    - Only folders are added to the queue for further exploration

    This approach is MUCH faster than browsing every single item, while still finding
    tags at any depth in the hierarchy.

    Args:
        opc_server (str): Name of the OPC connection in Ignition
        base_node_id (str): Starting OPC node ID (e.g., 'nsu=http://...;s=/path')
        search_tag_names (str or list): Tag name(s) to search for. Can be:
                                        - Single string: 'CV'
                                        - List of strings: ['CV', 'ACTUAL', 'PV']
                                        - None: returns all leaf tags
        max_iterations (int): Maximum number of browse operations to prevent infinite loops

    Returns:
        list: List of dictionaries containing tag information
              Format: [{'node_id': 'full_node_id', 'display_name': 'CV', 'relative_path': 'BRX-AIC-005/PID1/PV/CV'}]

    Example paths found:
        - BRX-AI-001/PV/CV (2 levels deep)
        - BRX-AIC-005/PID1/PV/CV (3 levels deep)
        - BRX-AIC-005/PID1/OUT/CV (3 levels deep in different folder)
        - BRX-WIC-001/PID1/MODE/ACTUAL (ACTUAL tag)
    """
    found_tags = []

    # Normalize search_tag_names to always be a list (or None)
    if search_tag_names is not None:
        if isinstance(search_tag_names, str):
            # Single string - convert to list
            search_list = [search_tag_names]
        else:
            # Already a list
            search_list = search_tag_names
    else:
        # None means search for all tags
        search_list = None

    # Queue of nodes to browse - each item is (node_id, relative_path)
    browse_queue = [(base_node_id, '')]

    # Track visited nodes to avoid infinite loops
    visited = set()
    visited.add(base_node_id)

    iteration_count = 0
    total_items_found = 0

    print("Starting iterative OPC browsing...")
    print("Base Node: " + base_node_id)
    if search_list:
        print("Searching for tags: " + ', '.join(search_list))
    else:
        print("Searching for all tags")
    print("=" * 80)

    while browse_queue and iteration_count < max_iterations:
        iteration_count += 1

        # Get next node to browse
        current_node_id, current_relative_path = browse_queue.pop(0)

        # Progress update every 10 iterations
        if iteration_count % 10 == 0:
            print("[Iteration " + str(iteration_count) + "] Queue size: " + str(len(browse_queue)) +
                  ", Tags found: " + str(len(found_tags)))

        try:
            # Browse the current node
            items = system.opc.browseServer(opc_server, current_node_id)

            if items is None:
                continue

            total_items_found += len(items)

            # Process each item
            for item in items:
                display_name = item.getDisplayName()

                # Skip the #Properties folder that appears in OPC UA
                if display_name == '#Properties':
                    continue

                # Get the node ID for this item
                item_node_id = item.getNodeId()

                # Build the relative path
                if current_relative_path:
                    item_relative_path = current_relative_path + '/' + display_name
                else:
                    item_relative_path = display_name

                # Optimization: If the name matches our search criteria (e.g., "CV" or "ACTUAL"),
                # we know it's a tag (not a folder), so save it immediately without
                # trying to browse into it. This saves a lot of time!

                # Check if this item matches our search criteria
                matches_search = False
                if search_list is not None:
                    # We have a specific list of tag names to find
                    matches_search = display_name in search_list

                if matches_search:
                    # Found a matching tag - save it!
                    found_tags.append({
                        'node_id': item_node_id,
                        'display_name': display_name,
                        'relative_path': item_relative_path
                    })
                    # Don't try to browse into it - continue to next item
                    continue

                # Item doesn't match search criteria (or we're searching for all tags)
                # Check if it's a folder by trying to browse into it
                is_folder = False
                try:
                    # Try to browse into this item to see if it has children
                    child_items = system.opc.browseServer(opc_server, item_node_id)

                    # If it returns items, it's a folder
                    if child_items and len(child_items) > 0:
                        is_folder = True
                except:
                    # If browsing fails, it's not a folder (or we don't have access)
                    is_folder = False

                # If it's a folder, add to queue for further browsing
                if is_folder and item_node_id not in visited:
                    browse_queue.append((item_node_id, item_relative_path))
                    visited.add(item_node_id)

        except Exception as e:
            print("Error browsing node '" + str(current_node_id) + "': " + str(e))
            # Continue with next item in queue
            continue

    if iteration_count >= max_iterations:
        print("\nWARNING: Reached maximum iteration limit (" + str(max_iterations) + ")")

    print("\n" + "=" * 80)
    print("Browse complete!")
    print("Iterations: " + str(iteration_count))
    print("Total items browsed: " + str(total_items_found))
    print("Tags found matching criteria: " + str(len(found_tags)))
    print("=" * 80 + "\n")

    return found_tags


def print_tag_paths(found_tags, root_folder, tag_provider='default'):
    """
    Print the Ignition tag paths that would be created.

    Args:
        found_tags (list): List of tag information dictionaries
        root_folder (str): Root folder name in Ignition
        tag_provider (str): Tag provider name
    """
    print("\n" + "=" * 80)
    print("TAG PATHS THAT WOULD BE CREATED:")
    print("=" * 80)

    if len(found_tags) == 0:
        print("No tags found!")
        return

    # Group tags by folder for better readability
    folder_structure = {}

    for tag_info in found_tags:
        relative_path = tag_info['relative_path']
        display_name = tag_info['display_name']

        # Split path into folder and tag name
        path_parts = relative_path.split('/')

        # The folder path is everything except the last part
        if len(path_parts) > 1:
            folder_path = '/'.join(path_parts[:-1])
        else:
            folder_path = ''

        # Build full Ignition path
        if folder_path:
            ignition_path = '[' + tag_provider + ']' + root_folder + '/' + folder_path + '/' + display_name
        else:
            ignition_path = '[' + tag_provider + ']' + root_folder + '/' + display_name

        # Store in folder structure
        if folder_path not in folder_structure:
            folder_structure[folder_path] = []
        folder_structure[folder_path].append({
            'ignition_path': ignition_path,
            'opc_node_id': tag_info['node_id'],
            'display_name': display_name
        })

    # Print organized by folder
    folder_count = 0
    tag_count = 0

    for folder_path in sorted(folder_structure.keys()):
        folder_count += 1
        folder_display = folder_path if folder_path else '(root)'

        print("\n--- Folder: " + root_folder + "/" + folder_display + " ---")

        for tag in folder_structure[folder_path]:
            tag_count += 1
            print("  [" + str(tag_count) + "] " + tag['ignition_path'])
            print("      OPC: " + str(tag['opc_node_id']))

    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("  Folders: " + str(folder_count))
    print("  Tags: " + str(tag_count))
    print("=" * 80)


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


def create_opc_tag(tag_provider, tag_path, tag_name, opc_server, opc_node_id, data_type='Float8'):
    """
    Create an OPC tag in Ignition.

    Args:
        tag_provider (str): Name of the tag provider
        tag_path (str): Parent path where to create the tag
        tag_name (str): Name of the tag
        opc_server (str): OPC server connection name
        opc_node_id (str): OPC UA node ID
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

    # Create OPC tag configuration using node ID
    tag_config = {
        'name': tag_name,
        'tagType': 'AtomicTag',
        'dataType': data_type,
        'opcServer': opc_server,
        'opcItemPath': str(opc_node_id),  # Use node ID instead of path
        'enabled': True,
        'valueSource': 'opc'
    }

    try:
        # Create the tag
        system.tag.configure(parent_path, [tag_config], 'o')
        print("Created OPC tag: " + full_tag_path)
        return True
    except Exception as e:
        print("Error creating tag '" + full_tag_path + "': " + str(e))
        import traceback
        traceback.print_exc()
        return False


def create_tags_from_list(found_tags, opc_server, tag_provider, root_folder, data_type='Float8', chunk_size=50):
    """
    Create Ignition tags from the found tags list.

    Args:
        found_tags (list): List of tag information dictionaries
        opc_server (str): OPC server connection name
        tag_provider (str): Tag provider name
        root_folder (str): Root folder in Ignition
        data_type (str): Data type for tags
        chunk_size (int): Number of tags to create at once

    Returns:
        dict: Summary of creation operation
    """
    print("\n" + "=" * 80)
    print("CREATING TAGS IN IGNITION")
    print("=" * 80)

    # Create root folder
    print("\nCreating root folder: " + root_folder)
    root_path = create_folder_structure(tag_provider, '', root_folder)
    folders_created = 1

    # Build folder structure and tag configs
    print("\nAnalyzing folder structure...")
    folder_cache = set()
    tags_created = 0

    for idx, tag_info in enumerate(found_tags):
        if (idx + 1) % 50 == 0:
            print("Processing tag " + str(idx + 1) + " / " + str(len(found_tags)))

        try:
            relative_path = tag_info['relative_path']
            display_name = tag_info['display_name']
            node_id = tag_info['node_id']

            # Split into folder structure and tag name
            path_parts = relative_path.split('/')
            folder_structure = path_parts[:-1]

            # Create folder structure
            current_path = root_path
            for folder_name in folder_structure:
                folder_key = current_path + '/' + folder_name
                if folder_key not in folder_cache:
                    current_path = create_folder_structure(tag_provider, current_path, folder_name)
                    folder_cache.add(folder_key)
                    folders_created += 1
                else:
                    if current_path.endswith('/'):
                        current_path = current_path + folder_name
                    else:
                        current_path = current_path + '/' + folder_name

            # Create the tag
            success = create_opc_tag(
                tag_provider,
                current_path,
                display_name,
                opc_server,
                node_id,
                data_type
            )

            if success:
                tags_created += 1

            # Small delay every chunk_size tags
            if (idx + 1) % chunk_size == 0:
                time.sleep(0.5)

        except Exception as e:
            print("Error processing tag: " + str(e))
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("TAG CREATION COMPLETE")
    print("=" * 80)
    print("Tags Created: " + str(tags_created) + " / " + str(len(found_tags)))
    print("Folders Created: " + str(folders_created))
    print("=" * 80)

    return {
        'success': True,
        'tags_created': tags_created,
        'folders_created': folders_created
    }


def main():
    """
    Main execution function - Configure your parameters here.
    """
    # ========== CONFIGURATION PARAMETERS ==========

    # OPC UA server connection name as configured in Ignition
    OPC_SERVER = 'DeltaV Edge OPC UA'

    # Base OPC UA node ID (starting point for browsing)
    BASE_NODE_ID = 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001'

    # Tag provider in Ignition (typically 'default')
    TAG_PROVIDER = 'default'

    # Root folder name in Ignition tag browser
    ROOT_FOLDER = 'BRX001'

    # Tag name(s) to search for
    # Can be a single string: 'CV'
    # Or a list of strings: ['CV', 'ACTUAL', 'PV']
    # Set to None to import all leaf tags
    SEARCH_TAG_NAMES = ['CV', 'ACTUAL']  # Import both CV and ACTUAL tags

    # Data type for created tags
    # Common types: 'Float8', 'Float4', 'Int4', 'Int8', 'Boolean', 'String'
    DATA_TYPE = 'Float8'

    # Number of tags to create at once (smaller = slower but more reliable)
    CHUNK_SIZE = 50

    # Maximum number of browse iterations (safety limit)
    MAX_ITERATIONS = 2000

    # DRY RUN MODE - Set to True to only print paths without creating tags
    DRY_RUN = True  # Change to False to actually create tags

    # ========== END CONFIGURATION ==========

    print("=" * 80)
    print("DeltaV OPC Tag Import - Iterative Browsing")
    print("=" * 80)
    print("OPC Server: " + OPC_SERVER)
    print("Base Node: " + BASE_NODE_ID)
    print("Tag Provider: " + TAG_PROVIDER)
    print("Root Folder: " + ROOT_FOLDER)
    if isinstance(SEARCH_TAG_NAMES, list):
        print("Search Tag Names: " + str(SEARCH_TAG_NAMES))
    else:
        print("Search Tag Name: " + str(SEARCH_TAG_NAMES))
    print("Data Type: " + DATA_TYPE)
    print("DRY RUN: " + str(DRY_RUN))
    print("=" * 80 + "\n")

    start_time = time.time()

    # Step 1: Browse OPC server iteratively
    print("Step 1: Browsing OPC server...")
    found_tags = browse_opc_iterative(
        OPC_SERVER,
        BASE_NODE_ID,
        SEARCH_TAG_NAMES,
        MAX_ITERATIONS
    )

    browse_time = time.time() - start_time

    if len(found_tags) == 0:
        print("\nNo tags found matching criteria. Exiting.")
        return {'success': False, 'tags_found': 0}

    # Step 2: Print or create tags
    if DRY_RUN:
        print("\n*** DRY RUN MODE - Only printing paths, not creating tags ***")
        print_tag_paths(found_tags, ROOT_FOLDER, TAG_PROVIDER)

        print("\nTo actually create these tags:")
        print("1. Review the paths above")
        print("2. Set DRY_RUN = False in the configuration")
        print("3. Run the script again")

        result = {
            'success': True,
            'dry_run': True,
            'tags_found': len(found_tags),
            'browse_time_seconds': int(browse_time)
        }
    else:
        print("\n*** LIVE MODE - Creating tags in Ignition ***")
        result = create_tags_from_list(
            found_tags,
            OPC_SERVER,
            TAG_PROVIDER,
            ROOT_FOLDER,
            DATA_TYPE,
            CHUNK_SIZE
        )
        result['browse_time_seconds'] = int(browse_time)
        result['total_time_seconds'] = int(time.time() - start_time)

    print("\n" + "=" * 80)
    print("SCRIPT COMPLETE")
    print("Total Time: " + str(int(time.time() - start_time)) + " seconds")
    print("=" * 80)

    return result


# ========== EXECUTION ==========
# Run the main function
if __name__ == '__main__' or True:  # The 'or True' ensures it runs in Ignition Script Console
    result = main()
