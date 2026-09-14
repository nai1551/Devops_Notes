// routes/todos.js
// A small REST API for managing todos. Each route is deliberately kept
// simple and commented so it's easy to follow as a learning example.

import { Router } from 'express';
import db from '../db.js';

const router = Router();

// GET /api/todos  -> list all todos, newest first
router.get('/', (req, res) => {
  const todos = db.prepare('SELECT * FROM todos ORDER BY id DESC').all();
  res.json(todos);
});

// POST /api/todos  -> create a new todo
// body: { "title": "Buy milk" }
router.post('/', (req, res) => {
  const { title } = req.body;

  if (!title || !title.trim()) {
    return res.status(400).json({ error: 'title is required' });
  }

  const result = db
    .prepare('INSERT INTO todos (title, done) VALUES (?, 0)')
    .run(title.trim());

  const newTodo = db
    .prepare('SELECT * FROM todos WHERE id = ?')
    .get(result.lastInsertRowid);

  res.status(201).json(newTodo);
});

// PATCH /api/todos/:id  -> toggle or update a todo
// body: { "done": true }  or  { "title": "New title" }
router.patch('/:id', (req, res) => {
  const { id } = req.params;
  const existing = db.prepare('SELECT * FROM todos WHERE id = ?').get(id);

  if (!existing) {
    return res.status(404).json({ error: 'todo not found' });
  }

  const title = req.body.title !== undefined ? req.body.title : existing.title;
  const done =
    req.body.done !== undefined ? (req.body.done ? 1 : 0) : existing.done;

  db.prepare('UPDATE todos SET title = ?, done = ? WHERE id = ?').run(
    title,
    done,
    id
  );

  const updated = db.prepare('SELECT * FROM todos WHERE id = ?').get(id);
  res.json(updated);
});

// DELETE /api/todos/:id  -> remove a todo
router.delete('/:id', (req, res) => {
  const { id } = req.params;
  const existing = db.prepare('SELECT * FROM todos WHERE id = ?').get(id);

  if (!existing) {
    return res.status(404).json({ error: 'todo not found' });
  }

  db.prepare('DELETE FROM todos WHERE id = ?').run(id);
  res.status(204).send();
});

export default router;
