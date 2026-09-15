# Simple Todo App

A minimal full-stack practice project: **Node.js + Express + SQLite** backend,
plain **HTML/CSS/JS** frontend (no React, no build step). Built for practicing
full-stack basics and CI/CD (GitHub Actions + Jenkins).

## Stack

- **Backend:** Node.js, Express 5, better-sqlite3 (file-based SQLite database)
- **Frontend:** Plain HTML/CSS/JS served as static files by Express
- **Tests:** Jest + Supertest (API tests)

## Project structure

```
simple-todo-app/
├── server.js           # Express app entry point
├── db.js                # SQLite database setup
├── routes/
│   └── todos.js          # REST API routes (GET/POST/PATCH/DELETE)
├── public/               # Static frontend (served directly, no build step)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── __tests__/
│   └── todos.test.js     # API tests
└── package.json
```

## Getting started

```bash
npm install
npm start
```

Then open http://localhost:3000 in your browser.

## Running tests

```bash
npm test
```

This runs Jest + Supertest against the Express app directly (no server needs
to be running separately).

## API

| Method | Route             | Body                          | Description          |
|--------|-------------------|--------------------------------|-----------------------|
| GET    | `/api/todos`       | -                              | List all todos        |
| POST   | `/api/todos`       | `{ "title": "..." }`           | Create a todo          |
| PATCH  | `/api/todos/:id`   | `{ "done": true }` or `{ "title": "..." }` | Update a todo |
| DELETE | `/api/todos/:id`   | -                              | Delete a todo          |

## Next steps to practice

- Add a `PUT` route or validation middleware
- Add due dates or priority levels to todos
- Swap the plain JS frontend for React (this project intentionally avoids
  that so you can add it yourself as a next step)
- Wire up GitHub Actions / Jenkins CI (see `.github/workflows/ci.yml` and
  `Jenkinsfile` if present)
