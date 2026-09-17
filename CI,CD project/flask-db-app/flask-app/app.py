from flask import Flask, request
import mysql.connector

app = Flask(__name__)

db_config = {
    "host": "db-container",
    "user": "flaskuser",
    "password": "flaskpass",
    "database": "mydb"
}

def get_connection():
    return mysql.connector.connect(**db_config)

def ensure_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message VARCHAR(255)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        message = request.form.get("message")
        if message:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (message) VALUES (%s)", (message,))
            conn.commit()
            cursor.close()
            conn.close()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, message FROM notes ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    rows_html = "".join(f"<li>#{r[0]}: {r[1]}</li>" for r in rows)

    return f"""
    <h2>Add a note</h2>
    <form method="POST">
        <input type="text" name="message" placeholder="Type something...">
        <button type="submit">Save</button>
    </form>
    <h3>Saved notes:</h3>
    <ul>{rows_html}</ul>
    """

if __name__ == "__main__":
    ensure_table()
    app.run(host="0.0.0.0", port=5000)
