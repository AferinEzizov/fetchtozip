# FetchtoZip

**FetchtoZip** is a high-performance, API-driven microservice built with Python for fetching, processing, and exporting data (in ZIP or other formats) from HTTP sources. The system is designed for asynchronous operation and is optimized for fast, scalable tabular data processing.

## Key Features

- **API-Driven Workflow**: Exposes RESTful endpoints for all operations—adding inputs, configuring processing, starting tasks, checking status, and downloading results.
- **Dynamic Input Management**: Add, update, list, or clear data column definitions via API.
- **Configurable Processing**: Set processing parameters and export formats through dedicated configuration endpoints.
- **Asynchronous Task Execution**: Launch data processing jobs as background tasks, enabling non-blocking, concurrent operations.
- **Status & Control**: Query the status of any task or cancel it if needed.
- **Data Fetching**: Pulls data from HTTP endpoints using a configurable source URL.
- **Fast Data Processing**: Uses [Polars](https://www.pola.rs/) for efficient columnar data transformation, filtering, and grouping—much faster than pandas.
- **Multiple Export Formats**: Output can be CSV, JSON, XLSX, or ZIP, as selected in the configuration.
- **Download API**: Retrieve results via `/download/{task_id}` endpoint in the requested format.
- **Temporary File Management**: All intermediate and result files are managed in a configurable temp directory.
- **Error Handling & Progress**: Tracks task progress, handles errors gracefully, and provides detailed status.
- **WebSocket Support**: (If enabled) Real-time task progress notifications via WebSocket.
- **Modular Python Structure**: Code is split into logical modules—API routing, core config, pipeline services, export utilities, and data models.
- **Docker Deployment**: Easily containerizable with environment variables for all configs.
## Requirments
- Python 3.9+
- pip or conda
- Docker (for containerized deployment)

# FetchtoZip API Usage Guide

This guide will help you interact efficiently with the FetchtoZip microservice REST API, explaining every endpoint, typical usage, and request/response structure.

---

## Overview

**FetchtoZip** is an API-driven microservice for fetching, processing, and exporting data—primarily to ZIP (or other formats like CSV, JSON, XLSX). Designed for automation and integration, all operations are accessible via clear REST endpoints. The system supports asynchronous background tasks, temporary file management, real-time progress (via WebSocket), and robust error/status tracking.

---

## API Endpoints Explained

### 1. **Column Input Management**

#### Add/Update a Single Input
- **POST** `/api/export/inputs`
- **Purpose:** Add or update a single column definition for processing.
- **Request Body:** JSON, matching the `Input` schema:
  ```json
  {
    "name": "column_name",     // (string, required) Name of the column
    "column": 1,               // (integer, required) Index or identifier
    "change_order": 1          // (integer, optional) Order of transformation
  }
  ```
- **Response:** Success message, plus the added/updated input.

#### Add/Update Multiple Inputs
- **POST** `/api/export/bulk-inputs`
- **Purpose:** Bulk add or update multiple columns.
- **Request Body:** JSON array of `Input` objects.
  ```json
  [
    { "name": "a", "column": 1, "change_order": 1 },
    { "name": "b", "column": 2, "change_order": 2 }
  ]
  ```
- **Response:** Success message and count of inputs added/updated.

#### List All Inputs
- **GET** `/api/export/inputs-list`
- **Purpose:** Retrieve the current list of all defined column inputs.
- **Response:** JSON object with the list and count.

#### Clear All Inputs
- **DELETE** `/api/export/inputs-clear`
- **Purpose:** Remove all defined column inputs.
- **Response:** Success message.

---

### 2. **Processing Configuration**

#### Set Processing Configuration
- **POST** `/api/export/configure`
- **Purpose:** Set up data source, export type, limits, and other processing parameters.
- **Request Body:** JSON, matching the `Configure` schema:
  ```json
  {
    "file_type": "zip",       // (string, required) Export format (zip, csv, json, xlsx)
    "tmp_dir": "./temp",      // (string, optional) Temporary directory path
    "rate_limit": 10,         // (integer, optional) Source fetch rate limit
    "page_limit": 100,        // (integer, optional) Max pages to process
    "db_url": null            // (string, optional) Database URL, if used
  }
  ```
- **Response:** Success message and the stored config.

---

### 3. **Task Processing**

#### Start a Processing Task
- **POST** `/api/export/start`
- **Purpose:** Launches a background job using current inputs and config.
- **Response:** Success message and a unique `task_id`.

#### Get Task Status
- **GET** `/api/export/status/{task_id}`
- **Purpose:** Check the progress, state, or errors of a specific processing task.
- **Path Parameter:** `task_id` (string, required)
- **Response:** JSON with task status, progress, or error details.

#### Cancel a Task
- **DELETE** `/api/export/cancel/{task_id}`
- **Purpose:** Attempt to cancel a running background task.
- **Path Parameter:** `task_id` (string, required)
- **Response:** Success or error message.

---

### 4. **Output Download**

#### Download Result File
- **GET** `/api/export/download/{task_id}`
- **Purpose:** Download the processed file for a completed task.
- **Path Parameter:** `task_id` (string, required)
- **Response:** Typically a file stream (ZIP, CSV, JSON, XLSX), or an error if not ready.

---

### 5. **WebSocket (Optional)**
- **WS** `/api/export/ws/{task_id}`
- **Purpose:** Subscribe for real-time progress updates for a task.

---

## Request/Response Conventions

- **Content-Type:** Always use `application/json` for POST requests.
- **Validation Errors:** 422 responses will contain error details.
- **Success:** 200 responses indicate successful operation.
- **Task IDs:** Returned by `/start`, required for all status, download, and cancel operations.

---

## Example Usage

Add a column input:
```bash
curl -X POST "http://localhost:8000/api/export/inputs" \
  -H "Content-Type: application/json" \
  -d '{"name": "revenue", "column": 3, "change_order": 1}'
```

Bulk add columns:
```bash
curl -X POST "http://localhost:8000/api/export/bulk-inputs" \
  -H "Content-Type: application/json" \
  -d '[{"name": "a", "column": 1}, {"name": "b", "column": 2}]'
```

Set export config:
```bash
curl -X POST "http://localhost:8000/api/export/configure" \
  -H "Content-Type: application/json" \
  -d '{"file_type": "zip", "rate_limit": 10, "page_limit": 100}'
```

Start processing:
```bash
curl -X POST "http://localhost:8000/api/export/start"
```

Check task status:
```bash
curl "http://localhost:8000/api/export/status/<task_id>"
```

Download result:
```bash
curl -O "http://localhost:8000/api/export/download/<task_id>"
```

---

## Schemas

### Input

| Field         | Type    | Description                     |
|---------------|---------|---------------------------------|
| name          | string  | Name of the column              |
| column        | integer | Column index or identifier      |
| change_order  | integer | (Optional) Order for processing |

### Configure

| Field      | Type    | Description                          |
|------------|---------|--------------------------------------|
| file_type  | string  | Output format: zip, csv, json, xlsx  |
| tmp_dir    | string  | Temp directory for file storage      |
| rate_limit | integer | HTTP fetch rate limit                |
| page_limit | integer | Max number of pages to process       |
| db_url     | string  | (Optional) Database URL              |

---

## General Best Practices

- **Always configure your inputs and processing before starting a task.**
- **Use the status endpoint to monitor tasks and know when downloads are ready.**
- **Use the cancel endpoint to stop long-running or unnecessary tasks.**
- **Use the WebSocket for real-time updates if needed.**
- **Handle validation errors by reading the error message and correcting your request data.**

---

**For further details, see the OpenAPI schema or the [project README](https://github.com/AferinEzizov/fetchtozip/blob/main/README.md).**


**Author**: [Aferin Ezizov](https://github.com/AferinEzizov)
