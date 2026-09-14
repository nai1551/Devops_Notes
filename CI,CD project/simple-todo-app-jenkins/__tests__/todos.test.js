// __tests__/todos.test.js
// Basic API tests using Jest + Supertest. Run with: npm test
// NODE_ENV=test stops the server from actually listening on a port,
// so supertest can drive the Express app in-memory.

import request from 'supertest';
import app from '../server.js';
import db from '../db.js';

beforeEach(() => {
  // Start each test with a clean table
  db.exec('DELETE FROM todos');
});

afterAll(() => {
  db.close();
});

describe('GET /api/todos', () => {
  test('returns an empty list initially', async () => {
    const res = await request(app).get('/api/todos');
    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });
});

describe('POST /api/todos', () => {
  test('creates a new todo', async () => {
    const res = await request(app)
      .post('/api/todos')
      .send({ title: 'Learn Jenkins' });

    expect(res.status).toBe(201);
    expect(res.body.title).toBe('Learn Jenkins');
    expect(res.body.done).toBe(0);
  });

  test('rejects an empty title', async () => {
    const res = await request(app).post('/api/todos').send({ title: '  ' });
    expect(res.status).toBe(400);
  });
});

describe('PATCH /api/todos/:id', () => {
  test('marks a todo as done', async () => {
    const created = await request(app)
      .post('/api/todos')
      .send({ title: 'Write tests' });

    const res = await request(app)
      .patch(`/api/todos/${created.body.id}`)
      .send({ done: true });

    expect(res.status).toBe(200);
    expect(res.body.done).toBe(1);
  });

  test('returns 404 for a missing todo', async () => {
    const res = await request(app).patch('/api/todos/9999').send({ done: true });
    expect(res.status).toBe(404);
  });
});

describe('DELETE /api/todos/:id', () => {
  test('deletes a todo', async () => {
    const created = await request(app)
      .post('/api/todos')
      .send({ title: 'Temporary' });

    const res = await request(app).delete(`/api/todos/${created.body.id}`);
    expect(res.status).toBe(204);

    const list = await request(app).get('/api/todos');
    expect(list.body).toEqual([]);
  });
});
