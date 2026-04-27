/**
 * Eisenhower Task Dashboard Server
 * Express + WebSocket for real-time updates
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const chokidar = require('chokidar');
const path = require('path');
const fs = require('fs');
const { loadAllTasks } = require('./parser');

// Parse command line arguments for port
function parseArgs() {
  const args = process.argv.slice(2);
  let port = 8080;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--port' && args[i + 1]) {
      port = parseInt(args[i + 1], 10);
      i++;
    }
  }

  return { port };
}

const { port } = parseArgs();
const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Serve static files from public directory
app.use(express.static(path.join(__dirname, 'public')));

// API endpoint to get all tasks
app.get('/api/tasks', (req, res) => {
  const data = loadAllTasks();
  res.json(data);
});

// API endpoint for health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// WebSocket connection handling
const clients = new Set();

wss.on('connection', (ws) => {
  console.log('[WebSocket] Client connected');
  clients.add(ws);

  // Send initial data
  const initialData = loadAllTasks();
  ws.send(JSON.stringify({ type: 'init', data: initialData }));

  ws.on('close', () => {
    console.log('[WebSocket] Client disconnected');
    clients.delete(ws);
  });

  ws.on('error', (err) => {
    console.error('[WebSocket] Error:', err);
    clients.delete(ws);
  });
});

// Broadcast data to all connected clients
function broadcast(data) {
  const message = JSON.stringify({ type: 'update', data });
  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}

// Watch for file changes
// Tasks are located in workspace/tasks/ directory
const tasksDir = path.join(__dirname, '../../..', 'tasks');
const watchFiles = [
  path.join(tasksDir, 'tasks.md'),
  path.join(tasksDir, 'customer-projects.md'),
  path.join(tasksDir, 'delegation.md'),
  path.join(tasksDir, 'maybe.md')
];

console.log('[Watcher] Watching files:');
watchFiles.forEach(f => console.log(`  - ${f}`));

const watcher = chokidar.watch(watchFiles, {
  persistent: true,
  ignoreInitial: true,
  usePolling: false,
  interval: 1000
});

let debounceTimer = null;

watcher.on('change', (filePath) => {
  console.log(`[Watcher] File changed: ${path.basename(filePath)}`);

  // Debounce to avoid multiple rapid updates
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  debounceTimer = setTimeout(() => {
    console.log('[Watcher] Broadcasting update to clients');
    const data = loadAllTasks();
    broadcast(data);
  }, 500);
});

watcher.on('error', (error) => {
  console.error('[Watcher] Error:', error);
});

// Save port to config file for next time
const PORT_FILE = path.join(__dirname, 'port.conf');
fs.writeFileSync(PORT_FILE, port.toString());

// Start server
server.listen(port, () => {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║  Eisenhower Task Dashboard                                 ║
╠════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:${port}                   ║
║  API endpoint:      http://localhost:${port}/api/tasks         ║
║  WebSocket:         ws://localhost:${port}                     ║
╚════════════════════════════════════════════════════════════╝
  `);
});

// Handle server startup errors (e.g., port already in use)
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`[Error] Port ${port} is already in use. Please use a different port with: ./start.sh --port <port>`);
  } else {
    console.error('[Error] Server error:', err);
  }
  process.exit(1);
});

// Global error handlers to prevent crashes
process.on('uncaughtException', (err) => {
  console.error('[Fatal] Uncaught Exception:', err);
  // Don't exit immediately, try to keep running
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('[Fatal] Unhandled Rejection at:', promise, 'reason:', reason);
  // Don't exit immediately, try to keep running
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n[Server] SIGINT received, shutting down gracefully...');
  watcher.close();
  wss.close();
  server.close(() => {
    console.log('[Server] Closed');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('\n[Server] SIGTERM received, shutting down gracefully...');
  watcher.close();
  wss.close();
  server.close(() => {
    console.log('[Server] Closed');
    process.exit(0);
  });
});
