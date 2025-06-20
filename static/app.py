import asyncio
import json
from pyodide.http import pyfetch, WebSocket
from pyscript import Element, document
from js import console, setTimeout, downloadFile # Import JS functions

# --- Global State (Simplified for PyScript) ---
STORED_DB_CONFIGS = [] # This would ideally be fetched from backend for persistence
ACTIVE_CONFIG = {}
STORED_INPUTS = []
WEBSOCKET_CONNECTED = False

# --- Helper Functions ---

def display_notification(message, type="info"):
    """Displays a notification message on the UI."""
    notifications_div = Element("notifications")
    notification_item = document.createElement("div")
    notification_item.className = f"notification-item {type}"
    notification_item.innerText = message
    notifications_div.element.prepend(notification_item) # Add to top

    # Automatically remove after 5 seconds
    def remove_notification():
        notifications_div.element.removeChild(notification_item)
    setTimeout(remove_notification, 5000)

def show_loading():
    # Simple loading indicator
    display_notification("Processing request...", type="info")

def hide_loading():
    # Placeholder for hiding loading indicator
    pass

async def fetch_json(url, method="GET", body=None):
    """Generic function to make API calls and handle JSON response."""
    show_loading()
    try:
        kwargs = {"method": method}
        if body:
            kwargs["body"] = json.dumps(body)
            kwargs["headers"] = {"Content-Type": "application/json"}

        response = await pyfetch(url, **kwargs)

        if response.ok:
            return await response.json()
        else:
            error_detail = await response.json()
            error_msg = error_detail.get("detail", "An unknown error occurred.")
            console.error(f"API Error ({response.status}): {error_msg}")
            display_notification(f"Error: {error_msg}", type="error")
            return None
    except Exception as e:
        console.error(f"Network or JSON parsing error: {e}")
        display_notification(f"Network error: {e}", type="error")
        return None
    finally:
        hide_loading()

def update_db_choice_dropdowns():
    """Updates the DB selection dropdowns with currently stored DBs."""
    db_config_dropdown = Element("config-db-choice")
    fetch_db_dropdown = Element("fetch-db-choice")

    # Clear existing options
    db_config_dropdown.element.innerHTML = "<option value=''>-- Select a Stored DB --</option>"
    fetch_db_dropdown.element.innerHTML = "<option value=''>-- Select a Stored DB --</option>"

    # Add options for each stored DB
    for db in STORED_DB_CONFIGS:
        option = document.createElement("option")
        option_value = json.dumps(db) # Store full DB config as value for easy retrieval
        option.value = option_value
        if "db_file_path" in db: # Local DB
            option.innerText = f"Local: {db['db_file_path']}"
        else: # External DB
            option.innerText = f"External: {db['db_type']} - {db['db_name']}@{db['host']}"
        db_config_dropdown.element.appendChild(option)
        fetch_db_dropdown.element.appendChild(option.cloneNode(True)) # Clone for the other dropdown

# --- API Interaction Functions ---

async def add_or_update_external_db(event):
    db_data = {
        "db_type": Element("ext-db-type").value,
        "username": Element("ext-username").value,
        "password": Element("ext-password").value,
        "host": Element("ext-host").value,
        "port": Element("ext-port").value,
        "db_name": Element("ext-db-name").value,
        "sql_query": Element("ext-sql-query").value,
        "driver": Element("ext-driver").value or None,
    }
    response = await fetch_json("/api/db_management/db/external", "POST", db_data)
    if response:
        display_notification(f"External DB Config Added/Updated: {response.get('message')}")
        await list_all_db_configs(None) # Refresh list
    else:
        display_notification("Failed to add/update external DB config.", type="error")

async def add_or_update_local_db(event):
    db_data = {
        "db_file_path": Element("local-db-path").value,
        "initial_sql": Element("local-initial-sql").value or None,
        "sql_query": Element("local-sql-query").value,
    }
    response = await fetch_json("/api/db_management/db/local", "POST", db_data)
    if response:
        display_notification(f"Local DB Config Added/Updated: {response.get('message')}")
        await list_all_db_configs(None) # Refresh list
    else:
        display_notification("Failed to add/update local DB config.", type="error")

async def list_all_db_configs(event):
    global STORED_DB_CONFIGS
    response = await fetch_json("/api/db_management/db/list", "GET")
    if response:
        Element("db-list-output").element.innerText = json.dumps(response, indent=2)
        STORED_DB_CONFIGS = response.get("external_db_configs", []) + response.get("local_db_configs", [])
        update_db_choice_dropdowns()
        display_notification("DB configurations listed.")
    else:
        display_notification("Failed to list DB configs.", type="error")

async def clear_all_db_configs(event):
    response = await fetch_json("/api/db_management/db/clear/all", "DELETE")
    if response:
        display_notification(f"All DB Configs Cleared: {response.get('message')}")
        Element("db-list-output").element.innerText = ""
        global STORED_DB_CONFIGS
        STORED_DB_CONFIGS = []
        update_db_choice_dropdowns()
    else:
        display_notification("Failed to clear all DB configs.", type="error")

async def set_active_configuration(event):
    global ACTIVE_CONFIG
    file_type = Element("config-file-type").value
    tmp_dir = Element("config-tmp-dir").value or None
    selected_db_json = Element("config-db-choice").value

    db_config_for_active_config = None
    if selected_db_json:
        try:
            db_config_for_active_config = json.loads(selected_db_json)
        except json.JSONDecodeError:
            display_notification("Invalid JSON for selected DB configuration.", type="error")
            return

    config_data = {
        "file_type": file_type,
        "tmp_dir": tmp_dir,
        "db_config": db_config_for_active_config # This can be null
    }

    response = await fetch_json("/api/config/configure", "POST", config_data)
    if response:
        ACTIVE_CONFIG = response.get("active_configuration", {})
        display_notification(f"Active Configuration Set: {response.get('message')}")
        Element("active-config-output").element.innerText = json.dumps(ACTIVE_CONFIG, indent=2)
    else:
        display_notification("Failed to set active configuration.", type="error")

async def get_active_configuration(event):
    global ACTIVE_CONFIG
    response = await fetch_json("/api/config/configure/active", "GET")
    if response:
        ACTIVE_CONFIG = response.get("active_configuration", {})
        Element("active-config-output").element.innerText = json.dumps(ACTIVE_CONFIG, indent=2)
        display_notification("Active configuration retrieved.")
    else:
        display_notification("Failed to get active configuration.", type="error")

async def add_bulk_inputs(event):
    inputs_json_str = Element("inputs-json").value
    try:
        inputs_data = json.loads(inputs_json_str)
        if not isinstance(inputs_data, list):
            raise ValueError("Input must be a JSON array of input objects.")
    except (json.JSONDecodeError, ValueError) as e:
        display_notification(f"Invalid JSON for inputs: {e}", type="error")
        return

    response = await fetch_json("/api/config/inputs/bulk", "POST", inputs_data)
    if response:
        display_notification(f"Inputs Added/Updated: {response.get('message')}")
        await list_all_inputs(None)
    else:
        display_notification("Failed to add/update bulk inputs.", type="error")

async def list_all_inputs(event):
    global STORED_INPUTS
    response = await fetch_json("/api/config/inputs/list", "GET")
    if response:
        Element("inputs-list-output").element.innerText = json.dumps(response, indent=2)
        STORED_INPUTS = response.get("inputs", [])
        display_notification("Inputs listed.")
    else:
        display_notification("Failed to list inputs.", type="error")

async def clear_all_inputs(event):
    response = await fetch_json("/api/config/inputs/clear", "DELETE")
    if response:
        display_notification(f"All Inputs Cleared: {response.get('message')}")
        Element("inputs-list-output").element.innerText = ""
        global STORED_INPUTS
        STORED_INPUTS = []
    else:
        display_notification("Failed to clear all inputs.", type="error")

async def fetch_table_data(event):
    selected_db_json = Element("fetch-db-choice").value
    sql_query_for_fetch = Element("fetch-sql-query").value

    db_config_for_fetch = None
    if selected_db_json:
        try:
            db_config_for_fetch = json.loads(selected_db_json)
            # Override SQL query if provided in the input field
            db_config_for_fetch["sql_query"] = sql_query_for_fetch
        except json.JSONDecodeError:
            display_notification("Invalid JSON for selected DB configuration.", type="error")
            return
    else:
        display_notification("Please select a DB configuration or enter a new one for fetching.", type="error")
        return

    if not sql_query_for_fetch:
         display_notification("SQL Query is required for fetching data.", type="error")
         return


    response = await fetch_json("/api/tables/table/data", "POST", db_config_for_fetch)
    if response and response.get("data"):
        data = response["data"]
        display_table(data)
        display_notification(f"Fetched {len(data)} rows of data.")
        Element("btn-export-current-data").element.style.display = "block" # Show export button
    else:
        Element("data-table-container").element.innerHTML = "<p>No data fetched or an error occurred.</p>"
        Element("btn-export-current-data").element.style.display = "none" # Hide export button
        display_notification("Failed to fetch table data.", type="error")

def display_table(data):
    """Renders a simple HTML table from a list of dictionaries."""
    if not data:
        Element("data-table-container").element.innerHTML = "<p>No data to display.</p>"
        return

    table_html = "<table class='data-table'><thead><tr>"
    headers = list(data[0].keys())
    for header in headers:
        table_html += f"<th>{header}</th>"
    table_html += "</tr></thead><tbody>"

    for row in data:
        table_html += "<tr>"
        for header in headers:
            table_html += f"<td>{row.get(header, '')}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"

    Element("data-table-container").element.innerHTML = table_html

async def export_current_data(event):
    """Exports the currently displayed data as JSON."""
    # For simplicity, we'll re-fetch the data or rely on a global variable if performance allows
    # In a real app, you'd want to hold the fetched data in a PyScript global variable
    # This example assumes `current_fetched_data` is available from `fetch_table_data`
    # You might need to refine how `current_fetched_data` is maintained.
    # For now, we'll just download what's currently in the data-table-container (if we parsed it)
    # A more robust solution would be to use the `data` variable from `fetch_table_data`
    # and stringify it, then trigger a JS download.

    # This is a very simplified export. In a real app, you might re-call the pipeline
    # with `file_type='json'` or `file_type='xlsx'` if you want server-side export.

    # If you want to export the data currently displayed in the table (which is simple JSON here)
    # you'd need to store the `data` from `fetch_table_data` in a global variable.
    # Let's assume `_current_displayed_data` is populated by `fetch_table_data`
    global _current_displayed_data
    if '_current_displayed_data' in globals() and _current_displayed_data:
        json_data = json.dumps(_current_displayed_data, indent=2)
        # Use the JS function to trigger a download
        downloadFile(f"data:application/json;charset=utf-8,{encodeURIComponent(json_data)}", "exported_data.json")
        display_notification("Current data exported as JSON.", type="info")
    else:
        display_notification("No data to export.", type="error")


async def trigger_pipeline(event):
    task_id = Element("pipeline-task-id").value or None # If you add a field for task_id
    # Using the currently active config and stored inputs for simplicity
    if not ACTIVE_CONFIG:
        display_notification("Please set an active configuration first.", type="error")
        return
    if not STORED_INPUTS:
        display_notification("Please add some column inputs first.", type="error")
        # return # Allow pipeline with no inputs

    pipeline_request = {
        "task_id": task_id,
        "inputs": STORED_INPUTS,
        "configuration": ACTIVE_CONFIG
    }
    response = await fetch_json("/api/pipeline/run", "POST", pipeline_request)
    if response:
        task_id = response.get("task_id")
        output_path = response.get("output_path")
        display_notification(f"Pipeline triggered! Task ID: {task_id}. Output Path: {output_path}")
        if task_id:
            # You would likely want a button or link to download this.
            # For demonstration, let's create a link for immediate download if it's a file
            download_url = f"/api/downloads/downloads/download/{task_id}"
            display_notification(f"<a href='{download_url}' target='_blank'>Download {task_id}.zip</a> (This link might not work directly if file is not ready instantly)", type="info")

    else:
        display_notification("Failed to trigger pipeline.", type="error")


# --- WebSocket for Notifications ---
async def connect_websocket():
    global WEBSOCKET_CONNECTED
    if WEBSOCKET_CONNECTED:
        return

    try:
        # Assuming your FastAPI server has a WebSocket endpoint, e.g., /ws
        # If your PyScript is served from localhost:8000, and FastAPI from localhost:8000,
        # you might need to adjust this depending on your reverse proxy setup.
        # For simplicity, if FastAPI is running on the same host/port:
        ws_url = f"ws://{document.location.host}/ws" # Or specify exact host:port if different

        # If using AWS, this would be ws://your-ec2-public-ip/ws
        # Or wss:// for secure WebSocket (recommended for production)
        # ws_url = f"wss://your-ec2-public-ip/ws"

        ws = await WebSocket.new(ws_url)
        WEBSOCKET_CONNECTED = True
        display_notification("Connected to real-time notifications.", type="info")
        console.log("WebSocket connected!")

        async for msg in ws:
            if msg.type == "message":
                try:
                    notification_data = json.loads(msg.data)
                    message_type = notification_data.get("type", "info")
                    message_content = notification_data.get("message", "Unknown notification")
                    display_notification(f"WS: {message_content}", type=message_type)
                except json.JSONDecodeError:
                    display_notification(f"WS Raw: {msg.data}", type="info")
            elif msg.type == "close":
                WEBSOCKET_CONNECTED = False
                display_notification("Disconnected from real-time notifications.", type="error")
                console.log("WebSocket disconnected.")
                # Optional: Reconnect after a delay
                await asyncio.sleep(5)
                await connect_websocket()
            elif msg.type == "error":
                WEBSCRIPT_CONNECTED = False
                display_notification("WebSocket error occurred.", type="error")
                console.error("WebSocket error:", msg.data)

    except Exception as e:
        WEBSOCKET_CONNECTED = False
        display_notification(f"Failed to connect to WebSocket: {e}", type="error")
        console.error("WebSocket connection error:", e)

# --- Event Listeners and Initial Setup ---
@document.addEventListener("DOMContentLoaded")
async def setup_page(event):
    Element("btn-add-ext-db").element.onclick = add_or_update_external_db
    Element("btn-add-local-db").element.onclick = add_or_update_local_db
    Element("btn-list-dbs").element.onclick = list_all_db_configs
    Element("btn-clear-all-dbs").element.onclick = clear_all_db_configs
    Element("btn-set-active-config").element.onclick = set_active_configuration
    Element("btn-get-active-config").element.onclick = get_active_configuration
    Element("btn-add-bulk-inputs").element.onclick = add_bulk_inputs
    Element("btn-list-inputs").element.onclick = list_all_inputs
    Element("btn-clear-all-inputs").element.onclick = clear_all_inputs
    Element("btn-fetch-table-data").element.onclick = fetch_table_data
    Element("btn-export-current-data").element.onclick = export_current_data
    Element("btn-run-pipeline").element.onclick = trigger_pipeline
    # You'd add listeners for 'Save Current Config' and 'Tasks/Downloads'

    # Initial data loads
    await list_all_db_configs(None)
    await get_active_configuration(None)
    await list_all_inputs(None)

    # Start WebSocket connection
    await connect_websocket()

# Expose current_fetched_data for export (simple way, not ideal for large data)
_current_displayed_data = [] # Global to hold data for export
def set_current_displayed_data(data):
    global _current_displayed_data
    _current_displayed_data = data

# Modify fetch_table_data to populate _current_displayed_data
async def fetch_table_data_with_export(event):
    # ... (same fetching logic) ...
    response = await fetch_json("/api/tables/table/data", "POST", db_config_for_fetch)
    if response and response.get("data"):
        data = response["data"]
        set_current_displayed_data(data) # Store for export
        display_table(data)
        display_notification(f"Fetched {len(data)} rows of data.")
        Element("btn-export-current-data").element.style.display = "block"
    else:
        # ... (error handling) ...
        set_current_displayed_data([]) # Clear on error
        Element("btn-export-current-data").element.style.display = "none"

# Re-assign the event listener to the modified function
Element("btn-fetch-table-data").element.onclick = fetch_table_data_with_export

# To make encodeURIComponent available in Python
from js import encodeURIComponent
