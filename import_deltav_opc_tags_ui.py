"""
Ignition Script: DeltaV OPC Tag Import - UI Version with Progress Callbacks
Version 2.3 - Nested Root Folders, Auto Data Type Detection, and Real-time UI Progress Updates

This version is designed to run from a Perspective view with real-time progress updates
displayed in the UI. It uses callback functions to send status messages back to the view.

V2.3 Features (NEW):
    - Nested root folders: Use paths like 'DELTAV_SYSTEM/BIOREACTOR/CELL_CULTURE/BRX001'
      Result: [default]DELTAV_SYSTEM/BIOREACTOR/CELL_CULTURE/BRX001/BRX-AGIT-CTL/A_PV/CV
    - Automatic data type detection: Pass data_type=None to read actual OPC data types
      (Float8, Int4, Boolean, String) instead of using a fixed type

Usage:
    See PERSPECTIVE_VIEW_SETUP.md for how to create the UI and call this script.
"""

import time


def detect_opc_data_type(opc_server, opc_node_id):
    """
    Detect the OPC UA data type and map it to an Ignition data type.

    Args:
        opc_server (str): OPC server connection name
        opc_node_id (str): OPC UA node ID

    Returns:
        str: Ignition data type (e.g., 'Float8', 'Int4', 'Boolean', 'String')
    """
    try:
        # Try to read the current value from OPC to determine type
        value = system.opc.readValue(opc_server, str(opc_node_id))

        if value is not None:
            # Get the Python type of the value
            value_type = type(value).__name__

            # Map Python/Java types to Ignition data types
            type_map = {
                'float': 'Float8',
                'java.lang.Float': 'Float4',
                'java.lang.Double': 'Float8',
                'int': 'Int4',
                'long': 'Int8',
                'java.lang.Integer': 'Int4',
                'java.lang.Long': 'Int8',
                'bool': 'Boolean',
                'java.lang.Boolean': 'Boolean',
                'str': 'String',
                'unicode': 'String',
                'java.lang.String': 'String'
            }

            # Try to match the type
            for key, ignition_type in type_map.items():
                if key.lower() in value_type.lower():
                    return ignition_type

        # Default to Float8 if we can't determine
        return 'Float8'

    except Exception as e:
        # If we can't read the value, default to Float8
        return 'Float8'


def create_nested_folders(tag_provider, root_folder_path, progress_callback=None):
    """
    Create a nested folder structure from a path like 'DELTAV_SYSTEM/BIOREACTOR/BRX001'.

    Args:
        tag_provider (str): Tag provider name
        root_folder_path (str): Path with '/' separators (e.g., 'DELTAV_SYSTEM/BIOREACTOR/BRX001')
        progress_callback (function): Function to call with progress messages

    Returns:
        str: Full path to the deepest folder
    """
    # Split the path into individual folder names
    folders = root_folder_path.split('/')

    current_path = ''

    for folder_name in folders:
        folder_name = folder_name.strip()
        if not folder_name:
            continue

        # Build the full path for checking existence
        if current_path:
            if current_path.endswith('/'):
                new_path = current_path + folder_name
            else:
                new_path = current_path + '/' + folder_name
        else:
            new_path = folder_name

        full_path_with_provider = '[' + tag_provider + ']' + new_path

        # Check if folder already exists
        if not system.tag.exists(full_path_with_provider):
            # Create the folder
            folder_config = {
                'name': folder_name,
                'tagType': 'Folder'
            }

            config_parent = '[' + tag_provider + ']' + current_path if current_path else '[' + tag_provider + ']'

            try:
                system.tag.configure(config_parent, [folder_config], 'o')
                log_message(progress_callback, "Created folder: " + full_path_with_provider)
            except Exception as e:
                log_message(progress_callback, "Error creating folder '" + full_path_with_provider + "': " + str(e))

        current_path = new_path

    return current_path


def log_message(callback, message):
    """
    Helper function to send a log message via callback or print to console.

    Args:
        callback (function): Function to call with the message, or None to print
        message (str): The message to log
    """
    if callback:
        callback(message)
    else:
        print(message)


def browse_opc_iterative_ui(opc_server, base_node_id, search_tag_names=None, max_iterations=1000, progress_callback=None):
    """
    UI-friendly version of browse_opc_iterative with progress callbacks.

    Args:
        opc_server (str): Name of the OPC connection in Ignition
        base_node_id (str): Starting OPC node ID
        search_tag_names (str or list): Tag name(s) to search for
        max_iterations (int): Maximum number of browse operations
        progress_callback (function): Function to call with progress messages

    Returns:
        list: List of found tags
    """
    found_tags = []

    # Normalize search_tag_names to always be a list (or None)
    if search_tag_names is not None:
        if isinstance(search_tag_names, str):
            search_list = [search_tag_names]
        else:
            search_list = search_tag_names
    else:
        search_list = None

    browse_queue = [(base_node_id, '')]
    visited = set()
    visited.add(base_node_id)

    iteration_count = 0
    total_items_found = 0

    log_message(progress_callback, "Starting iterative OPC browsing...")
    log_message(progress_callback, "Base Node: " + base_node_id)
    if search_list:
        log_message(progress_callback, "Searching for tags: " + ', '.join(search_list))
    else:
        log_message(progress_callback, "Searching for all tags")
    log_message(progress_callback, "=" * 80)

    while browse_queue and iteration_count < max_iterations:
        iteration_count += 1

        current_node_id, current_relative_path = browse_queue.pop(0)

        # Progress update every 10 iterations
        if iteration_count % 10 == 0:
            msg = "[Iteration " + str(iteration_count) + "] Queue size: " + str(len(browse_queue)) + ", Tags found: " + str(len(found_tags))
            log_message(progress_callback, msg)

        try:
            items = system.opc.browseServer(opc_server, current_node_id)

            if items is None:
                continue

            total_items_found += len(items)

            for item in items:
                display_name = item.getDisplayName()

                if display_name == '#Properties':
                    continue

                item_node_id = item.getNodeId()

                if current_relative_path:
                    item_relative_path = current_relative_path + '/' + display_name
                else:
                    item_relative_path = display_name

                matches_search = False
                if search_list is not None:
                    matches_search = display_name in search_list

                if matches_search:
                    found_tags.append({
                        'node_id': item_node_id,
                        'display_name': display_name,
                        'relative_path': item_relative_path,
                        'opc_server': opc_server  # Store server name for data type detection
                    })
                    continue

                is_folder = False
                try:
                    child_items = system.opc.browseServer(opc_server, item_node_id)
                    if child_items and len(child_items) > 0:
                        is_folder = True
                except:
                    is_folder = False

                if is_folder and item_node_id not in visited:
                    browse_queue.append((item_node_id, item_relative_path))
                    visited.add(item_node_id)

        except Exception as e:
            log_message(progress_callback, "Error browsing node '" + str(current_node_id) + "': " + str(e))
            continue

    if iteration_count >= max_iterations:
        log_message(progress_callback, "\nWARNING: Reached maximum iteration limit (" + str(max_iterations) + ")")

    log_message(progress_callback, "\n" + "=" * 80)
    log_message(progress_callback, "Browse complete!")
    log_message(progress_callback, "Iterations: " + str(iteration_count))
    log_message(progress_callback, "Total items browsed: " + str(total_items_found))
    log_message(progress_callback, "Tags found matching criteria: " + str(len(found_tags)))
    log_message(progress_callback, "=" * 80 + "\n")

    return found_tags


def create_folder_structure_ui(tag_provider, parent_path, folder_name, progress_callback=None):
    """
    UI-friendly version of create_folder_structure with progress callbacks.
    """
    if parent_path:
        if parent_path.endswith('/'):
            folder_path = parent_path + folder_name
        else:
            folder_path = parent_path + '/' + folder_name
    else:
        folder_path = folder_name

    if tag_provider:
        full_path = '[' + tag_provider + ']' + folder_path
    else:
        full_path = folder_path

    if system.tag.exists(full_path):
        return folder_path

    folder_config = {
        'name': folder_name,
        'tagType': 'Folder'
    }

    config_parent = '[' + tag_provider + ']' + parent_path if tag_provider else parent_path

    try:
        system.tag.configure(config_parent, [folder_config], 'o')
        log_message(progress_callback, "Created folder: " + full_path)
    except Exception as e:
        log_message(progress_callback, "Error creating folder '" + full_path + "': " + str(e))

    return folder_path


def create_opc_tag_ui(tag_provider, tag_path, tag_name, opc_server, opc_node_id, data_type=None, progress_callback=None):
    """
    UI-friendly version of create_opc_tag with progress callbacks.

    Args:
        tag_provider (str): Name of the tag provider
        tag_path (str): Parent path where to create the tag
        tag_name (str): Name of the tag
        opc_server (str): OPC server connection name
        opc_node_id (str): OPC UA node ID
        data_type (str): Data type for the tag. If None, will auto-detect from OPC server (default: None)
        progress_callback (function): Function to call with progress messages

    Returns:
        bool: True if successful, False otherwise
    """
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

    if system.tag.exists(full_tag_path):
        # Don't log every skipped tag to avoid spam
        return True

    # Auto-detect data type if not provided
    if data_type is None:
        data_type = detect_opc_data_type(opc_server, opc_node_id)
        # Only log auto-detection occasionally to avoid spam
        if len(tag_name) < 10:  # Short names like "CV", "ACTUAL"
            log_message(progress_callback, "Auto-detected data type for " + tag_name + ": " + data_type)

    tag_config = {
        'name': tag_name,
        'tagType': 'AtomicTag',
        'dataType': data_type,
        'opcServer': opc_server,
        'opcItemPath': str(opc_node_id),
        'enabled': True,
        'valueSource': 'opc'
    }

    try:
        system.tag.configure(parent_path, [tag_config], 'o')
        log_message(progress_callback, "Created OPC tag: " + full_tag_path)
        return True
    except Exception as e:
        log_message(progress_callback, "Error creating tag '" + full_tag_path + "': " + str(e))
        return False


def create_tags_from_list_ui(found_tags, opc_server, tag_provider, root_folder, data_type=None, chunk_size=50, progress_callback=None):
    """
    UI-friendly version of create_tags_from_list with progress callbacks.

    Args:
        found_tags (list): List of tag information dictionaries
        opc_server (str): OPC server connection name (only used if data_type is provided)
        tag_provider (str): Tag provider name
        root_folder (str): Root folder in Ignition. Can be:
                           - Simple: 'BRX001'
                           - Nested: 'DELTAV_SYSTEM/BIOREACTOR/CELL_CULTURE/BRX001'
        data_type (str): Data type for tags. If None, will auto-detect from OPC server (default: None)
        chunk_size (int): Number of tags to process before pausing
        progress_callback (function): Function to call with progress messages

    Returns:
        dict: Summary of creation operation
    """
    log_message(progress_callback, "\n" + "=" * 80)
    log_message(progress_callback, "CREATING TAGS IN IGNITION")
    log_message(progress_callback, "=" * 80)

    # Create root folder (supports nested paths like 'DELTAV_SYSTEM/BIOREACTOR/BRX001')
    log_message(progress_callback, "\nCreating root folder structure: " + root_folder)
    if '/' in root_folder:
        # Nested folder path - use create_nested_folders
        root_path = create_nested_folders(tag_provider, root_folder, progress_callback)
        # Count how many folders were created (split by '/')
        folders_created = len([f for f in root_folder.split('/') if f.strip()])
    else:
        # Simple single-level folder - use existing function
        root_path = create_folder_structure_ui(tag_provider, '', root_folder, progress_callback)
        folders_created = 1

    log_message(progress_callback, "\nAnalyzing folder structure...")
    folder_cache = set()
    tags_created = 0

    for idx, tag_info in enumerate(found_tags):
        if (idx + 1) % 50 == 0:
            log_message(progress_callback, "Processing tag " + str(idx + 1) + " / " + str(len(found_tags)))

        try:
            relative_path = tag_info['relative_path']
            display_name = tag_info['display_name']
            node_id = tag_info['node_id']
            # Get OPC server from tag_info (stored during browsing)
            tag_opc_server = tag_info.get('opc_server', opc_server)

            path_parts = relative_path.split('/')
            folder_structure = path_parts[:-1]

            current_path = root_path
            for folder_name in folder_structure:
                folder_key = current_path + '/' + folder_name
                if folder_key not in folder_cache:
                    current_path = create_folder_structure_ui(tag_provider, current_path, folder_name, progress_callback)
                    folder_cache.add(folder_key)
                    folders_created += 1
                else:
                    if current_path.endswith('/'):
                        current_path = current_path + folder_name
                    else:
                        current_path = current_path + '/' + folder_name

            # Create the tag with auto-detection if data_type is None
            success = create_opc_tag_ui(
                tag_provider,
                current_path,
                display_name,
                tag_opc_server,
                node_id,
                data_type,  # Pass None to auto-detect, or specific type to use that
                progress_callback
            )

            if success:
                tags_created += 1

            if (idx + 1) % chunk_size == 0:
                time.sleep(0.5)

        except Exception as e:
            log_message(progress_callback, "Error processing tag: " + str(e))

    log_message(progress_callback, "\n" + "=" * 80)
    log_message(progress_callback, "TAG CREATION COMPLETE")
    log_message(progress_callback, "=" * 80)
    log_message(progress_callback, "Tags Created: " + str(tags_created) + " / " + str(len(found_tags)))
    log_message(progress_callback, "Folders Created: " + str(folders_created))
    log_message(progress_callback, "=" * 80)

    return {
        'success': True,
        'tags_created': tags_created,
        'folders_created': folders_created
    }


def import_deltav_tags_ui(opc_server, base_node_id, tag_provider, root_folder, search_tag_names,
                          data_type=None, chunk_size=50, max_iterations=2000,
                          dry_run=True, progress_callback=None):
    """
    Main function for UI-based import with progress callbacks.

    Args:
        opc_server (str): OPC server connection name
        base_node_id (str): Base OPC node ID to start browsing from
        tag_provider (str): Ignition tag provider name
        root_folder (str): Root folder in Ignition. Can be:
                           - Simple: 'BRX001'
                           - Nested: 'DELTAV_SYSTEM/BIOREACTOR/CELL_CULTURE/BRX001'
        search_tag_names (str or list): Tag name(s) to search for
        data_type (str): Data type for created tags. If None, will auto-detect from OPC server (default: None)
        chunk_size (int): Number of tags to process before pausing
        max_iterations (int): Maximum browse iterations
        dry_run (bool): If True, only shows what would be created
        progress_callback (function): Function to call with progress messages

    Returns:
        dict: Summary of the import operation
    """
    log_message(progress_callback, "=" * 80)
    log_message(progress_callback, "DeltaV OPC Tag Import - UI Version V2.3")
    log_message(progress_callback, "=" * 80)
    log_message(progress_callback, "OPC Server: " + opc_server)
    log_message(progress_callback, "Base Node: " + base_node_id)
    log_message(progress_callback, "Tag Provider: " + tag_provider)
    log_message(progress_callback, "Root Folder: " + root_folder)

    if isinstance(search_tag_names, list):
        log_message(progress_callback, "Search Tag Names: " + str(search_tag_names))
    else:
        log_message(progress_callback, "Search Tag Name: " + str(search_tag_names))

    if data_type is None:
        log_message(progress_callback, "Data Type: Auto-detect from OPC server")
    else:
        log_message(progress_callback, "Data Type: " + data_type)

    log_message(progress_callback, "DRY RUN: " + str(dry_run))
    log_message(progress_callback, "=" * 80 + "\n")

    start_time = time.time()

    # Step 1: Browse OPC server
    log_message(progress_callback, "Step 1: Browsing OPC server...")
    found_tags = browse_opc_iterative_ui(
        opc_server,
        base_node_id,
        search_tag_names,
        max_iterations,
        progress_callback
    )

    browse_time = time.time() - start_time

    if len(found_tags) == 0:
        log_message(progress_callback, "\nNo tags found matching criteria. Exiting.")
        return {'success': False, 'tags_found': 0}

    # Step 2: Create or preview tags
    if dry_run:
        log_message(progress_callback, "\n*** DRY RUN MODE - Preview only ***")
        log_message(progress_callback, "\nFound " + str(len(found_tags)) + " matching tags")
        log_message(progress_callback, "Sample paths that would be created:")

        # Show first 10 as samples
        for i, tag_info in enumerate(found_tags[:10]):
            relative_path = tag_info['relative_path']
            ignition_path = '[' + tag_provider + ']' + root_folder + '/' + relative_path
            log_message(progress_callback, "  " + str(i+1) + ". " + ignition_path)

        if len(found_tags) > 10:
            log_message(progress_callback, "  ... and " + str(len(found_tags) - 10) + " more")

        log_message(progress_callback, "\nTo create these tags, set DRY_RUN = False and run again.")

        result = {
            'success': True,
            'dry_run': True,
            'tags_found': len(found_tags),
            'browse_time_seconds': int(browse_time)
        }
    else:
        log_message(progress_callback, "\n*** LIVE MODE - Creating tags ***")
        result = create_tags_from_list_ui(
            found_tags,
            opc_server,
            tag_provider,
            root_folder,
            data_type,
            chunk_size,
            progress_callback
        )
        result['browse_time_seconds'] = int(browse_time)
        result['total_time_seconds'] = int(time.time() - start_time)

    log_message(progress_callback, "\n" + "=" * 80)
    log_message(progress_callback, "SCRIPT COMPLETE")
    log_message(progress_callback, "Total Time: " + str(int(time.time() - start_time)) + " seconds")
    log_message(progress_callback, "=" * 80)

    return result
