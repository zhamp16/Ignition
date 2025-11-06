# Perspective View Setup Guide for DeltaV OPC Tag Import

## Overview

This guide shows how to run the DeltaV OPC tag import script from a Perspective view with real-time progress updates, without tying up your PC.

## Architecture

```
Perspective View (Client)
    ↓ Button Click
Message Handler (Gateway)
    ↓ Runs script asynchronously
Import Script (Gateway)
    ↓ Writes progress to memory tag
Memory Tag (Gateway)
    ↓ Binding
Markdown Component (Client) - Shows real-time updates!
```

## Step 1: Create Memory Tags for Progress

Create these memory tags in your tag provider (e.g., `[default]`):

### Tag Structure:
```
[default]OPC_Import/
├── Status          (String) - Current status message
├── Progress        (String) - All accumulated progress messages
├── IsRunning       (Boolean) - True while script is running
├── PercentComplete (Integer) - Progress percentage (0-100)
└── Config/
    ├── OpcServer      (String)
    ├── BaseNodeId     (String)
    ├── TagProvider    (String)
    ├── RootFolder     (String)
    ├── SearchTagNames (String) - JSON array like ["CV", "ACTUAL"]
    ├── DataType       (String)
    ├── DryRun         (Boolean)
    └── MaxIterations  (Integer)
```

### Quick Creation Script:

Run this once in the Script Console to create the memory tags:

```python
# Create folder structure
folder_config = {
    'name': 'OPC_Import',
    'tagType': 'Folder'
}
system.tag.configure('[default]', [folder_config], 'o')

# Create status tags
status_tags = [
    {'name': 'Status', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': 'Ready'},
    {'name': 'Progress', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': ''},
    {'name': 'IsRunning', 'tagType': 'AtomicTag', 'dataType': 'Boolean', 'value': False},
    {'name': 'PercentComplete', 'tagType': 'AtomicTag', 'dataType': 'Int4', 'value': 0}
]
system.tag.configure('[default]OPC_Import', status_tags, 'o')

# Create config folder and tags
config_folder = {'name': 'Config', 'tagType': 'Folder'}
system.tag.configure('[default]OPC_Import', [config_folder], 'o')

config_tags = [
    {'name': 'OpcServer', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': 'DeltaV Edge OPC UA'},
    {'name': 'BaseNodeId', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': 'nsu=http://inmation.com/UA/;s=/System/Core/DeltaVSystems/DELTAV_SYSTEM/ControlStrategies/BIOREACTOR/CELL_CULTURE/BRX001'},
    {'name': 'TagProvider', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': 'default'},
    {'name': 'RootFolder', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': 'BRX001'},
    {'name': 'SearchTagNames', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': '["CV", "ACTUAL"]'},
    {'name': 'DataType', 'tagType': 'AtomicTag', 'dataType': 'String', 'value': 'Float8'},
    {'name': 'DryRun', 'tagType': 'AtomicTag', 'dataType': 'Boolean', 'value': True},
    {'name': 'MaxIterations', 'tagType': 'AtomicTag', 'dataType': 'Int4', 'value': 2000}
]
system.tag.configure('[default]OPC_Import/Config', config_tags, 'o')

print("Memory tags created successfully!")
```

## Step 2: Add Import Functions to Project Library

Before creating the message handler, we need to make the import functions available:

1. Open **Ignition Designer**
2. In the **Project Browser**, expand **Scripting**
3. Right-click **Project Library** > **New Script**
4. Name it: `opc_import`
5. Copy the entire contents of `import_deltav_opc_tags_ui.py` and paste it into this script
6. **Save the project**

Now the functions will be available to the message handler directly via: `opc_import.import_deltav_tags_ui()`

**Important:** Make sure your gateway script project is set to this project so the project library is accessible.

## Step 3: Create the Gateway Message Handler

1. In the **Project Browser**, expand **Gateway Events**
2. Right-click **Message Handlers** > **New Message Handler**
3. Name it: `opc-import-handler`
4. Paste this script:

```python
# Message Handler: opc-import-handler
# Created in: Designer > Gateway Events > Message Handlers
# Function signature must be: handleMessage(payload)

# Import standard Python libraries (system.* libraries are available by default)
import time
import json

def update_progress(message):
	"""Write a progress message to the Progress tag"""
	try:
		# Get current progress
		current = system.tag.readBlocking(['[default]OPC_Import/Progress'])[0].value
		if current is None:
			current = ''

		# Append new message with timestamp
		timestamp = system.date.format(system.date.now(), 'HH:mm:ss')
		new_message = '[' + timestamp + '] ' + message + '\n'
		updated = current + new_message

		# Write back (keep last 10000 characters to prevent memory issues)
		if len(updated) > 10000:
			updated = updated[-10000:]

		system.tag.writeBlocking(['[default]OPC_Import/Progress', '[default]OPC_Import/Status'],
		                         [updated, message])
	except Exception as e:
		print('Error updating progress: ' + str(e))

def run_import_script():
	"""The actual import script - runs asynchronously"""
	try:
		# Set running flag
		system.tag.writeBlocking(['[default]OPC_Import/IsRunning', '[default]OPC_Import/Progress'],
		                         [True, ''])

		# Read configuration from tags
		config_paths = [
			'[default]OPC_Import/Config/OpcServer',
			'[default]OPC_Import/Config/BaseNodeId',
			'[default]OPC_Import/Config/TagProvider',
			'[default]OPC_Import/Config/RootFolder',
			'[default]OPC_Import/Config/SearchTagNames',
			'[default]OPC_Import/Config/DataType',
			'[default]OPC_Import/Config/DryRun',
			'[default]OPC_Import/Config/MaxIterations'
		]

		config_values = system.tag.readBlocking(config_paths)

		opc_server = config_values[0].value
		base_node_id = config_values[1].value
		tag_provider = config_values[2].value
		root_folder = config_values[3].value
		search_tag_names_json = config_values[4].value
		data_type = config_values[5].value
		dry_run = config_values[6].value
		max_iterations = config_values[7].value

		# Parse search tag names from JSON
		search_tag_names = json.loads(search_tag_names_json)

		update_progress('Starting DeltaV OPC Tag Import...')
		update_progress('OPC Server: ' + opc_server)
		update_progress('Base Node: ' + base_node_id)
		update_progress('Search Tags: ' + str(search_tag_names))
		update_progress('Dry Run: ' + str(dry_run))
		update_progress('=' * 80)

		# Call the import function from project library
		# No import needed - gateway script project is set to this project
		result = opc_import.import_deltav_tags_ui(
			opc_server=opc_server,
			base_node_id=base_node_id,
			tag_provider=tag_provider,
			root_folder=root_folder,
			search_tag_names=search_tag_names,
			data_type=data_type,
			chunk_size=50,
			max_iterations=max_iterations,
			dry_run=dry_run,
			progress_callback=update_progress
		)

		update_progress('\n' + '=' * 80)
		update_progress('IMPORT COMPLETE!')
		update_progress('Tags found: ' + str(result.get('tags_found', 0)))
		if not dry_run:
			update_progress('Tags created: ' + str(result.get('tags_created', 0)))
			update_progress('Folders created: ' + str(result.get('folders_created', 0)))
		update_progress('=' * 80)

	except Exception as e:
		update_progress('\nERROR: ' + str(e))
		import traceback
		update_progress(traceback.format_exc())
	finally:
		# Clear running flag
		system.tag.writeBlocking(['[default]OPC_Import/IsRunning', '[default]OPC_Import/PercentComplete'],
		                         [False, 100])

# ========== MAIN MESSAGE HANDLER FUNCTION ==========
# This is the required function signature for Ignition message handlers
def handleMessage(payload):
	"""
	Main message handler entry point.

	Args:
		payload (dict): Dictionary containing message data

	Returns:
		dict: Response dictionary
	"""
	# Get the action from payload (dictionary subscript)
	action = payload['action']

	if action == 'start_import':
		# Run the import script asynchronously so it doesn't block
		system.util.invokeAsynchronous(run_import_script)
		return {'status': 'started', 'message': 'Import started in background'}
	else:
		return {'status': 'error', 'message': 'Unknown action: ' + str(action)}
```

## Step 4: Create the Perspective View

### View JSON Structure:

Create a new view called `OPC_Tag_Import` with these components:

1. **Text Field** - OPC Server Name
   - Binding: Bidirectional to `[default]OPC_Import/Config/OpcServer`

2. **Text Field** - Base Node ID
   - Binding: Bidirectional to `[default]OPC_Import/Config/BaseNodeId`

3. **Text Field** - Root Folder
   - Binding: Bidirectional to `[default]OPC_Import/Config/RootFolder`

4. **Text Field** - Search Tag Names (JSON format)
   - Binding: Bidirectional to `[default]OPC_Import/Config/SearchTagNames`
   - Placeholder: `["CV", "ACTUAL"]`

5. **Toggle** - Dry Run Mode
   - Binding: Bidirectional to `[default]OPC_Import/Config/DryRun`

6. **Button** - Start Import
   - Enabled binding: `not {[default]OPC_Import/IsRunning}`
   - onClick script:

```python
# Button onClick script
system.perspective.sendMessage('opc-import-handler', {'action': 'start_import'})
```

7. **Button** - Clear Progress
   - onClick script:

```python
# Clear progress button
system.tag.writeBlocking(['[default]OPC_Import/Progress'], [''])
```

8. **Markdown Component** - Progress Display
   - Style: `monospace`, `white-space: pre-wrap`, `max-height: 600px`, `overflow-y: auto`
   - props.source binding: `{[default]OPC_Import/Progress}`

9. **Label** - Status
   - text binding: `{[default]OPC_Import/Status}`

10. **Circular Progress** (optional)
    - Show when running
    - visible binding: `{[default]OPC_Import/IsRunning}`

### Example View Layout:

```
┌─────────────────────────────────────────┐
│  DeltaV OPC Tag Import                  │
├─────────────────────────────────────────┤
│  OPC Server:    [DeltaV Edge OPC UA  ]  │
│  Base Node:     [nsu=http://...      ]  │
│  Root Folder:   [BRX001              ]  │
│  Search Tags:   [["CV", "ACTUAL"]    ]  │
│  Dry Run:       [✓]                     │
│                                          │
│  [Start Import]  [Clear Progress]       │
│                                          │
│  Status: Ready                           │
├─────────────────────────────────────────┤
│  Progress:                              │
│  ┌───────────────────────────────────┐ │
│  │ [11:23:45] Starting...            │ │
│  │ [11:23:46] Browsing OPC server... │ │
│  │ [11:23:50] [Iteration 10] ...     │ │
│  │ [11:24:00] [Iteration 50] ...     │ │
│  │ ...                                │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Step 5: Test the Setup

1. **First Test - Dry Run:**
   - Set Dry Run = True
   - Click "Start Import"
   - Watch the markdown component fill with real-time progress
   - You can close the view or navigate away - it keeps running!

2. **Check Progress Anytime:**
   - The progress is stored in the tag
   - Open the view again and see the full history

3. **Live Run:**
   - Review the dry run output
   - Set Dry Run = False
   - Click "Start Import" again
   - Watch tags being created in real-time

## Important Notes

### Project Library Access

**Gateway Script Project Setting:**
- In Gateway webpage > **Config** > **Scripting** > **Gateway Scripting Project**
- Set to the project containing your `opc_import` script
- This allows message handlers to access project library scripts directly

**How it works:**
- System libraries (`system.tag`, `system.util`, etc.) are available by default - no import needed
- Project library scripts are accessible directly: `opc_import.functionName()`
- Standard Python libraries (`time`, `json`, etc.) must be imported as usual

### If Script Fails

**NameError: name 'opc_import' is not defined:**
1. Verify gateway script project is set to your project
2. Script name in Project Library must be exactly `opc_import`
3. Save the project after adding the script
4. Restart gateway if needed

**Functions not found:**
1. Verify all functions are in the `opc_import` script
2. Check function names match (case-sensitive)
3. Make sure the script saved successfully

## Benefits of This Approach

✅ **Non-blocking**: Your PC is free, script runs on gateway
✅ **Real-time updates**: See progress as it happens
✅ **Resumable**: Can check progress anytime by opening the view
✅ **Historical**: All messages are saved in the tag
✅ **Safe**: Can't accidentally cancel by closing view
✅ **Configurable**: Change parameters without editing code

## Monitoring Long-Running Imports

For a 30-minute import:
- Progress updates every 10 iterations (~every 30 seconds)
- Status tag shows current operation
- Can open view, check progress, close it, come back later
- IsRunning tag shows if script is still active

## Troubleshooting

**Script doesn't start:**
- Check gateway logs: Gateway webpage > Status > Logs
- Verify message handler is enabled
- Check tag paths are correct

**No progress updates:**
- Verify memory tags exist
- Check tag write permissions
- Look for errors in gateway logs

**View doesn't update:**
- Check tag bindings in Perspective
- Refresh the view
- Check if IsRunning tag is updating

**Script timeout:**
- Gateway scripts have default timeout (check gateway settings)
- May need to adjust in Config > Gateway Settings > Gateway Scripts

## Next Steps

1. Create the memory tags (Step 1)
2. Set up the message handler (Step 2)
3. Build the Perspective view (Step 3)
4. Test with Dry Run first!
5. Monitor and enjoy hands-free importing!
