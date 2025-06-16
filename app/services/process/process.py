<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Fetch to Zip UI</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      display: flex;
      height: 100vh;
      background: #f4f4f4;
    }
    .sidebar {
      width: 260px;
      background: #333;
      color: white;
      padding: 1rem;
      overflow-y: auto;
    }
    .sidebar h2 {
      font-size: 1.5rem;
      margin-bottom: 1rem;
    }
    .sidebar label {
      display: block;
      margin-top: 10px;
    }
    .sidebar input {
      width: 100%;
      padding: 5px;
      margin-top: 4px;
    }
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .navbar {
      display: flex;
      justify-content: space-between;
      background: #222;
      padding: 1rem;
      color: white;
    }
    .navbar button {
      margin-left: 0.5rem;
      padding: 0.5rem 1rem;
      background: #444;
      border: none;
      color: white;
      cursor: pointer;
    }
    .content {
      padding: 1rem;
      overflow: auto;
    }
    .card {
      background: white;
      padding: 1rem;
      border-radius: 8px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
      margin-bottom: 1rem;
    }
    #toast {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #222;
      color: white;
      padding: 1rem;
      border-radius: 10px;
      display: none;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      text-align: left;
    }
    th {
      background-color: #f2f2f2;
      cursor: move;
    }
  </style>
</head>
<body>
  <div class="sidebar">
    <h2>Configuration</h2>
    <label>File Type<input type="text" id="file_type"></label>
    <label>Temp Dir<input type="text" id="tmp_dir"></label>
    <label>Rate Limit<input type="number" id="rate_limit"></label>
    <label>Page Limit<input type="number" id="page_limit"></label>
    <label>DB URL<input type="text" id="db_url" value="http://127.0.0.1:3001/api/data"></label>
    <button onclick="sendConfig()">Save Config</button>
    <hr>
    <h2>Input Data</h2>
    <label>Name<input type="text" id="input_name"></label>
    <label>Column<input type="number" id="input_column"></label>
    <label>Order<input type="number" id="input_order"></label>
    <button onclick="addInput()">Add Input</button>
    <button onclick="fetchInputs()">Refresh List</button>
  </div>
  <div class="main">
    <div class="navbar">
      <div>Topbar</div>
      <div>
        <button onclick="fetchInputs()">Fetch</button>
        <button onclick="clearInputs()">Clear</button>
        <button onclick="startProcess()">Start</button>
        <button onclick="downloadFile()">Download</button>
        <input type="text" id="task_id_input" placeholder="Task ID for status/download">
        <button onclick="getStatus()">Status</button>
        <button onclick="cancelTask()">Cancel</button>
        <button onclick="fetchDBTable()">Load Table</button>
      </div>
    </div>
    <div class="content">
      <div class="card">
        <h3>Inputs</h3>
        <ul id="inputs"></ul>
      </div>
      <div class="card">
        <h3>DB Table</h3>
        <table id="data_table"></table>
      </div>
    </div>
  </div>
  <div id="toast"></div>
  <script>
    function showToast(message) {
      const toast = document.getElementById('toast');
      toast.textContent = message;
      toast.style.display = 'block';
      setTimeout(() => toast.style.display = 'none', 3000);
    }

    async function fetchInputs() {
      const res = await fetch('http://localhost:8000/api/export/inputs-list');
      const data = await res.json();
      const list = document.getElementById('inputs');
      list.innerHTML = '';
      if (data && data.inputs) {
        data.inputs.forEach(input => {
          const li = document.createElement('li');
          li.textContent = `${input.name} - column: ${input.column}, order: ${input.change_order}`;
          list.appendChild(li);
        });
      }
      showToast('Fetched inputs');
    }

    async function clearInputs() {
      await fetch('http://localhost:8000/api/export/inputs-clear', { method: 'DELETE' });
      document.getElementById('inputs').innerHTML = '';
      showToast('Cleared inputs');
    }

    async function startProcess() {
      const res = await fetch('http://localhost:8000/api/export/start', { method: 'POST' });
      const data = await res.json();
      showToast('Started processing: ' + data.task_id);
      document.getElementById('task_id_input').value = data.task_id;
    }

    async function getStatus() {
      const taskId = document.getElementById('task_id_input').value;
      const res = await fetch(`http://localhost:8000/api/export/status/${taskId}`);
      const data = await res.json();
      showToast(`Status: ${data.status}`);
    }

    async function downloadFile() {
      const taskId = document.getElementById('task_id_input').value;
      window.location.href = `http://localhost:8000/api/export/download/${taskId}`;
      showToast('Download started');
    }

    async function cancelTask() {
      const taskId = document.getElementById('task_id_input').value;
      await fetch(`http://localhost:8000/api/export/cancel/${taskId}`, { method: 'DELETE' });
      showToast('Task cancelled');
    }

    async function addInput() {
      const body = {
        name: document.getElementById('input_name').value,
        column: parseInt(document.getElementById('input_column').value),
        change_order: parseInt(document.getElementById('input_order').value),
      };
      await fetch('http://localhost:8000/api/export/inputs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      fetchInputs();
      showToast('Input added');
    }

    async function sendConfig() {
      const config = {
        file_type: document.getElementById('file_type').value,
        tmp_dir: document.getElementById('tmp_dir').value,
        rate_limit: parseInt(document.getElementById('rate_limit').value),
        page_limit: parseInt(document.getElementById('page_limit').value),
        db_url: document.getElementById('db_url').value
      };
      await fetch('http://localhost:8000/api/export/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      showToast('Configuration saved');
    }

    async function fetchDBTable() {
      const url = document.getElementById('db_url').value;
      const res = await fetch(url);
      const data = await res.json();
      renderTable(data);
      showToast('Fetched table');
    }

    function renderTable(data) {
      const table = document.getElementById('data_table');
      if (!data || data.length === 0) return;
      const columns = Object.keys(data[0]);
      table.innerHTML = '';
      const thead = document.createElement('thead');
      const headRow = document.createElement('tr');

      columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        th.draggable = true;
        th.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', col));
        th.addEventListener('dragover', e => e.preventDefault());
        th.addEventListener('drop', e => {
          e.preventDefault();
          const fromCol = e.dataTransfer.getData('text/plain');
          const toCol = col;
          const fromIndex = columns.indexOf(fromCol);
          const toIndex = columns.indexOf(toCol);
          columns.splice(fromIndex, 1);
          columns.splice(toIndex, 0, fromCol);
          renderTable(data.map(row => {
            const newRow = {};
            columns.forEach(c => newRow[c] = row[c]);
            return newRow;
          }));
        });
        headRow.appendChild(th);
      });

      thead.appendChild(headRow);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      data.forEach(row => {
        const tr = document.createElement('tr');
        columns.forEach(col => {
          const td = document.createElement('td');
          td.textContent = row[col];
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
    }
  </script>
</body>
</html>
