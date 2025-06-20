from pyscript import document, display
import js
import asyncio

API_BASE = ""  # If you deploy under a subpath, set it here

def qs(id):
    return document.getElementById(id)

def set_html(id, html):
    qs(id).innerHTML = html

def show_tab(tab):
    for t in document.querySelectorAll(".tab"):
        t.classList.remove("active")
    for b in document.querySelectorAll(".tab-btn"):
        b.classList.remove("active")
    qs(f"tab-{tab}").classList.add("active")
    for b in document.querySelectorAll(".tab-btn"):
        if b.getAttribute("data-tab") == tab:
            b.classList.add("active")

def handle_tab_click(event):
    show_tab(event.target.getAttribute("data-tab"))

def setup_tabs():
    for btn in document.querySelectorAll(".tab-btn"):
        btn.addEventListener("click", handle_tab_click)
    show_tab("inputs")

#--------------------#
# API utility
#--------------------#
async def api_fetch(path, method="GET", data=None):
    url = API_BASE + path
    headers = {"Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = await js.fetch(url, { "method": "GET", "headers": headers })
        elif method == "DELETE":
            resp = await js.fetch(url, { "method": "DELETE", "headers": headers })
        else:
            resp = await js.fetch(url, {
                "method": method,
                "headers": headers,
                "body": js.JSON.stringify(data) if data else None
            })
        if resp.status == 204:
            return None
        if resp.headers.get("content-type", "").includes("application/json"):
            return await resp.json()
        elif resp.headers.get("content-type", "").includes("application/zip"):
            return await resp.arrayBuffer()
        else:
            return await resp.text()
    except Exception as e:
        return {"error": str(e)}

def toast(msg, typ="info"):
    js.console.log(f"{typ.upper()}: {msg}")
    js.window.alert(msg)

#--------------------#
# Inputs Tab
#--------------------#
async def refresh_inputs():
    res = await api_fetch("/api/config/inputs/list")
    if not res or "inputs" not in res:
        set_html("inputs-list", "<em>No stored inputs.</em>")
        return
    rows = []
    for inp in res["inputs"]:
        rows.append(f"<b>{inp.get('name')}</b> | Col: {inp.get('column')} | Order: {inp.get('change_order')}")
    set_html("inputs-list", "<br>".join(rows) or "<em>No stored inputs.</em>")

def on_input_form_submit(evt):
    evt.preventDefault()
    name = qs("input-name").value.strip()
    column = qs("input-column").value
    order = qs("input-order").value
    if not name or column == "":
        toast("Name and column index required.", "error")
        return
    data = {"name": name, "column": int(column)}
    if order != "": data["change_order"] = int(order)
    asyncio.ensure_future(add_or_update_input(data))

async def add_or_update_input(data):
    res = await api_fetch("/api/config/inputs", "POST", data)
    if "error" in res or res.get("detail"):
        toast("Failed to add/update input.", "error")
    else:
        toast("Input added/updated.", "info")
        await refresh_inputs()

def on_clear_inputs(evt):
    asyncio.ensure_future(clear_inputs())

async def clear_inputs():
    await api_fetch("/api/config/inputs/clear", "DELETE")
    await refresh_inputs()
    toast("All inputs cleared.", "info")

#--------------------#
# Config Tab
#--------------------#
def on_db_type_change(evt):
    if evt.target.value == "local":
        qs("local-db-fields").style.display = ""
        qs("external-db-fields").style.display = "none"
    else:
        qs("local-db-fields").style.display = "none"
        qs("external-db-fields").style.display = ""

def on_config_form_submit(evt):
    evt.preventDefault()
    file_type = qs("file-type").value
    tmp_dir = qs("tmp-dir").value.strip() or None
    db_type = [r for r in document.getElementsByName("db-type") if r.checked][0].value

    if db_type == "local":
        db_file_path = qs("local-db-path").value.strip() or ":memory:"
        initial_sql = qs("local-db-init").value.strip() or None
        sql_query = qs("local-db-query").value.strip()
        if not sql_query:
            toast("SQL query required.", "error")
            return
        db_config = {
            "db_file_path": db_file_path,
            "initial_sql": initial_sql,
            "sql_query": sql_query
        }
    else:
        db_type_val = qs("external-db-type").value.strip()
        username = qs("external-db-username").value.strip()
        password = qs("external-db-password").value
        host = qs("external-db-host").value.strip()
        port = qs("external-db-port").value.strip()
        db_name = qs("external-db-name").value.strip()
        sql_query = qs("external-db-query").value.strip()
        driver = qs("external-db-driver").value.strip() or None
        if not (db_type_val and username and password and host and port and db_name and sql_query):
            toast("Fill all external DB fields.", "error")
            return
        db_config = {
            "db_type": db_type_val,
            "username": username,
            "password": password,
            "host": host,
            "port": port,
            "db_name": db_name,
            "sql_query": sql_query,
            "driver": driver
        }

    data = {
        "file_type": file_type,
        "tmp_dir": tmp_dir,
        "db_config": db_config
    }
    asyncio.ensure_future(set_config(data))

async def set_config(data):
    res = await api_fetch("/api/config/configure", "POST", data)
    if "error" in res or res.get("detail"):
        toast("Failed to set config.", "error")
    else:
        toast("Active config set!", "info")
        await refresh_active_config()

async def refresh_active_config():
    res = await api_fetch("/api/config/configure/active")
    if not res or "configuration" not in res:
        set_html("active-config", "<em>No active config.</em>")
        return
    display_html = f"<pre>{js.JSON.stringify(res['configuration'], None, 2)}</pre>"
    set_html("active-config", display_html)

#--------------------#
# DB Management Tab
#--------------------#
def on_list_db(evt):
    asyncio.ensure_future(list_db())

async def list_db():
    res = await api_fetch("/api/db_management/db/list")
    if not res:
        set_html("db-list", "<em>No DB configs found.</em>")
        return
    html = f"<pre>{js.JSON.stringify(res, None, 2)}</pre>"
    set_html("db-list", html)

def on_clear_db_all(evt):    asyncio.ensure_future(clear_db_all())
def on_clear_db_external(evt): asyncio.ensure_future(clear_db_external())
def on_clear_db_local(evt):    asyncio.ensure_future(clear_db_local())

async def clear_db_all():
    await api_fetch("/api/db_management/db/clear/all", "DELETE")
    await list_db()
    toast("All DB configs cleared.", "info")

async def clear_db_external():
    await api_fetch("/api/db_management/db/clear/external", "DELETE")
    await list_db()
    toast("External DB configs cleared.", "info")

async def clear_db_local():
    await api_fetch("/api/db_management/db/clear/local", "DELETE")
    await list_db()
    toast("Local DB configs cleared.", "info")

#--------------------#
# Run Pipeline Tab
#--------------------#
def on_pipeline_form_submit(evt):
    evt.preventDefault()
    task_id = qs("pipeline-task-id").value.strip() or None
    asyncio.ensure_future(run_pipeline(task_id))

async def run_pipeline(task_id):
    # fetch current inputs and config
    res_inputs = await api_fetch("/api/config/inputs/list")
    res_config = await api_fetch("/api/config/configure/active")
    inputs = res_inputs.get("inputs", [])
    configuration = res_config.get("configuration")
    if not configuration:
        set_html("pipeline-result", "<em>No active configuration set.</em>")
        return
    payload = {
        "task_id": task_id,
        "inputs": inputs,
        "configuration": configuration
    }
    res = await api_fetch("/api/pipeline/run", "POST", payload)
    if "error" in res or res.get("detail"):
        set_html("pipeline-result", "<span style='color:red;'>Pipeline failed.</span>")
    else:
        html = "<b>Pipeline started:</b><br>" + "<br>".join(f"{k}: {v}" for k,v in res.items())
        set_html("pipeline-result", html)
        if "task_id" in res:
            # Save for download
            try:
                js.localStorage.setItem("last_task_id", res["task_id"])
            except Exception:
                pass

#--------------------#
# Downloads Tab
#--------------------#
def on_download_form_submit(evt):
    evt.preventDefault()
    task_id = qs("download-task-id").value.strip()
    if not task_id:
        toast("Task ID required.", "error")
        return
    asyncio.ensure_future(download_file(task_id))

async def download_file(task_id):
    set_html("download-result", f"Downloading file for task: <b>{task_id}</b> ...")
    url = f"{API_BASE}/api/downloads/downloads/download/{task_id}"
    try:
        resp = await js.fetch(url)
        if resp.status == 200 and resp.headers.get("content-type","").includes("application/zip"):
            buf = await resp.arrayBuffer()
            blob = js.window.Blob.new([buf], { "type": "application/zip" })
            url_obj = js.window.URL.createObjectURL(blob)
            a = js.document.createElement("a")
            a.href = url_obj
            a.download = f"result_{task_id}.zip"
            js.document.body.appendChild(a)
            a.click()
            js.document.body.removeChild(a)
            set_html("download-result", f"Download started for <b>{task_id}</b>.")
        else:
            set_html("download-result", "<span style='color:red;'>File not found or download failed.</span>")
    except Exception as e:
        set_html("download-result", "<span style='color:red;'>Error during download.</span>")

#--------------------#
# Setup on load
#--------------------#
def setup_events():
    # Tabs
    setup_tabs()
    # Inputs
    qs("input-form").addEventListener("submit", on_input_form_submit)
    qs("clear-inputs-btn").addEventListener("click", on_clear_inputs)
    # Config
    qs("config-form").addEventListener("submit", on_config_form_submit)
    for r in document.getElementsByName("db-type"):
        r.addEventListener("change", on_db_type_change)
    # DB
    qs("list-db-btn").addEventListener("click", on_list_db)
    qs("clear-db-all-btn").addEventListener("click", on_clear_db_all)
    qs("clear-db-external-btn").addEventListener("click", on_clear_db_external)
    qs("clear-db-local-btn").addEventListener("click", on_clear_db_local)
    # Pipeline
    qs("pipeline-form").addEventListener("submit", on_pipeline_form_submit)
    # Downloads
    qs("download-form").addEventListener("submit", on_download_form_submit)

def auto_fill_last_task_id():
    try:
        task_id = js.localStorage.getItem("last_task_id") or ""
        qs("download-task-id").value = task_id
    except Exception:
        pass

async def main():
    setup_events()
    await refresh_inputs()
    await refresh_active_config()
    auto_fill_last_task_id()

asyncio.ensure_future(main())
