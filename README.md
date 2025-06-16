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

## Core API Endpoints

| Method | Endpoint                   | Description                              |
|--------|----------------------------|------------------------------------------|
| POST   | `/api/export/inputs`       | Add or update a column input             |
| POST   | `/api/export/bulk-inputs`  | Add multiple column inputs               |
| GET    | `/api/export/inputs-list`  | List all stored inputs                   |
| DELETE | `/api/export/inputs-clear` | Clear all stored inputs                  |
| POST   | `/api/export/configure`    | Set the active processing configuration  |
| POST   | `/api/export/start`        | Start a new processing task (background) |
| GET    | `/api/export/status/{id}`  | Get the status of a processing task      |
| GET    | `/api/export/download/{id}`| Download the output of a completed task  |
| DELETE | `/api/export/cancel/{id}`  | Cancel a processing task                 |
| WS     | `/api/export/ws/{id}`      | (Optional) Real-time progress updates    |

## How It Works

1. **Define Inputs**: Specify columns and transformations via API.
2. **Configure Processing**: Set source URLs, processing options, and export format.
3. **Start Task**: Launch processing as a background job.
4. **Monitor Progress**: Poll status or listen for WebSocket notifications.
5. **Download Result**: Retrieve the finished file in your chosen format.

## Pipeline Architecture

- **Data Fetching**: Downloads data from the configured HTTP endpoint.
- **Processing**: Applies all transformations using Polars (column changes, filters, aggregations).
- **Export**: Writes results as CSV, JSON, XLSX, or creates a ZIP archive.
- **Cleanup**: Manages temp files, handles errors, and tracks each task’s state.
  
## Docker Image
[![Docker Pulls](https://img.shields.io/docker/aferin/fetchtozip.svg)](https://hub.docker.com/r/aferin/fetchtozip)

## Example Usage

```bash
# Add a new input column
curl -X POST "http://localhost:8000/api/export/inputs" \
  -H "Content-Type: application/json" \
  -d '{"name": "revenue", "column": 3, "change_order": 1}'

# Set configuration
curl -X POST "http://localhost:8000/api/export/configure" \
  -H "Content-Type: application/json" \
  -d '{"file_type": "zip", "rate_limit": 10, "page_limit": 100}'

# Start processing
curl -X POST "http://localhost:8000/api/export/start"

# Check status
curl "http://localhost:8000/api/export/status/task_abcdef123456"

# Download result (when completed)
curl -O "http://localhost:8000/api/export/download/task_abcdef123456"
```

## Project Structure

```
fetchtozip/
├── app/
│   ├── api/         # API routes and endpoints
│   ├── core/        # Configuration and parameters
│   ├── services/    # Pipeline, export, and processing logic
│   ├── models/      # Data schemas (Pydantic)
│   └── main.py      # FastAPI application entrypoint
├── temp/            # Temporary file storage
├── tests/           # Test suites
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.9+
- pip or conda
- Docker (for containerized deployment)

## Environment Variables

| Variable         | Description                       | Default     |
|------------------|-----------------------------------|-------------|
| `ENVIRONMENT`    | Deployment environment            | development |
| `LOG_LEVEL`      | Logging verbosity                 | info        |
| `TEMP_DIR`       | Directory for temporary files     | ./temp      |
| `MAX_FILE_SIZE`  | Maximum upload size (MB)          | 100         |
| `WORKER_TIMEOUT` | Background task timeout (seconds) | 300         |

## Running with Docker

```bash
docker build -t fetchtozip:latest .
docker run -d --name fetchtozip -p 8000:8000 -v $(pwd)/temp:/app/temp fetchtozip:latest
```

Or with Docker Compose:

```yaml
version: '3.8'
services:
  fetchtozip:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./temp:/app/temp
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
```

---

**License**: BSD 2-Clause  
**Author**: [Aferin Ezizov](https://github.com/AferinEzizov)
