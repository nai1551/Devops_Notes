// public/app.js
// Plain vanilla JS frontend - no framework, no build step. Talks to the
// Express API using fetch().

const form = document.getElementById('todo-form');
const input = document.getElementById('todo-input');
const list = document.getElementById('todo-list');

async function loadTodos() {
  const res = await fetch('/api/todos');
  const todos = await res.json();
  renderTodos(todos);
}

function renderTodos(todos) {
  list.innerHTML = '';

  todos.forEach((todo) => {
    const li = document.createElement('li');
    li.className = 'todo-item' + (todo.done ? ' done' : '');

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = !!todo.done;
    checkbox.addEventListener('change', () => toggleTodo(todo.id, checkbox.checked));

    const span = document.createElement('span');
    span.textContent = todo.title;

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.className = 'delete';
    deleteBtn.addEventListener('click', () => deleteTodo(todo.id));

    li.append(checkbox, span, deleteBtn);
    list.appendChild(li);
  });
}

async function addTodo(title) {
  await fetch('/api/todos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  await loadTodos();
}

async function toggleTodo(id, done) {
  await fetch(`/api/todos/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ done }),
  });
  await loadTodos();
}

async function deleteTodo(id) {
  await fetch(`/api/todos/${id}`, { method: 'DELETE' });
  await loadTodos();
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const title = input.value.trim();
  if (!title) return;
  input.value = '';
  addTodo(title);
});

loadTodos();
