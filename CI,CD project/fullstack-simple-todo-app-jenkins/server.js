// server.js
// Entry point: sets up Express, serves the static frontend from /public,
// and mounts the todos API under /api/todos.

import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import todosRouter from './routes/todos.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/api/todos', todosRouter);

// Only start listening when this file is run directly (not when imported
// by tests) - this makes the app easy to test with supertest.
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    console.log(`Todo app running at http://localhost:${PORT}`);
  });
}

export default app;
