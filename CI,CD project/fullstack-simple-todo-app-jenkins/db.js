// db.js
// Sets up a local SQLite database file and creates the "todos" table
// if it doesn't already exist. better-sqlite3 is synchronous, which
// keeps this tiny project easy to read - no callbacks or promises needed.

import Database from 'better-sqlite3';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.join(__dirname, 'todos.db');

const db = new Database(dbPath);

db.exec(`
  CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )
`);

export default db;
