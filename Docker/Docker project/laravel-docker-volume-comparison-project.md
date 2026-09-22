# Laravel + Docker: PHP 8.2, MySQL, File Uploads & Storage Comparison — Complete Project Guide

This documents a full project: a Laravel application built locally with PHP 8.2 and MySQL, containerized with Docker using an Nginx + PHP-FPM architecture, and used to run a direct, hands-on comparison between Docker **Named Volumes** and **Bind Mounts** for file storage.

---

## Project Goal

To understand how a Laravel application (PHP 8.2, Composer, a database, file uploads, and Docker storage) works together, and to practically demonstrate the difference between Docker Named Volumes and Bind Mounts — especially their behavior when containers are recreated or modified.

---

## Part 1: Local Environment Setup

### 1.1 Install PHP 8.2

Ubuntu's default repository ships a newer PHP version, so the Ondřej Surý PPA was used to get 8.2 specifically:

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:ondrej/php -y
sudo apt update
sudo apt install -y php8.2 php8.2-cli php8.2-common php8.2-mbstring php8.2-xml php8.2-bcmath php8.2-curl php8.2-mysql php8.2-zip php8.2-sqlite3
```

### 1.2 Install Composer

```bash
cd ~
curl -sS https://getcomposer.org/installer -o composer-setup.php
php composer-setup.php --install-dir=/usr/local/bin --filename=composer
rm composer-setup.php
```

### 1.3 Create the Laravel project

```bash
cd ~
composer create-project laravel/laravel laravel-demo
cd laravel-demo
```

### 1.4 Run bound to all interfaces

```bash
php artisan serve --host=0.0.0.0 --port=8000
```

`--host=0.0.0.0` makes the app reachable from outside the machine, not just from `localhost` inside it — the same principle used in the Flask project (`app.run(host="0.0.0.0")`).

### 1.5 Keep it running permanently with systemd

```bash
sudo nano /etc/systemd/system/laravel-dev.service
```

```ini
[Unit]
Description=Laravel Development Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/laravel-demo
ExecStart=/usr/bin/php artisan serve --host=0.0.0.0 --port=8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable laravel-dev
sudo systemctl start laravel-dev
```

### Real problem hit: `no such table: sessions`

Laravel's installer tried to create default database tables (including `sessions`) in SQLite during setup, but the SQLite PHP driver wasn't installed yet, so that migration silently failed. Every page request then crashed trying to read a `sessions` table that never existed.

**Fix applied:** Installed `php8.2-sqlite3`, and temporarily set `SESSION_DRIVER=file` in `.env` to unblock testing while MySQL was set up properly in Part 2.

---

## Part 2: Demo Application with a Database

### 2.1 Install MySQL

```bash
sudo apt install -y mysql-server
sudo systemctl enable mysql
sudo systemctl start mysql
```

### 2.2 Create a database and dedicated user

```bash
sudo mysql
```
```sql
CREATE DATABASE laravel_demo;
CREATE USER 'laravel_user'@'localhost' IDENTIFIED BY 'laravel_pass';
GRANT ALL PRIVILEGES ON laravel_demo.* TO 'laravel_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2.3 Point Laravel at MySQL

```bash
nano .env
```
```
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=laravel_demo
DB_USERNAME=laravel_user
DB_PASSWORD=laravel_pass
SESSION_DRIVER=database
```

### 2.4 Run migrations and create a demo table

```bash
php artisan config:clear
php artisan migrate
php artisan make:migration create_notes_table
```

Edit the generated migration's `up()` method:
```php
public function up(): void
{
    Schema::create('notes', function (Blueprint $table) {
        $table->id();
        $table->string('message');
        $table->timestamps();
    });
}
```

```bash
php artisan migrate
```

### 2.5 Add a test route to prove insert/retrieve works

```bash
nano routes/web.php
```
```php
use Illuminate\Support\Facades\DB;

Route::get('/notes', function () {
    DB::table('notes')->insert(['message' => 'Hello from MySQL!', 'created_at' => now(), 'updated_at' => now()]);
    $notes = DB::table('notes')->get();
    return $notes;
});
```

**Result confirmed:** Calling `curl http://localhost:8000/notes` repeatedly showed the row count growing (`id: 1, 2, 3, 4...`), proving genuine read/write against MySQL.

---

## Part 3: File Upload Functionality

### 3.1 Create the storage symlink

```bash
php artisan storage:link
```

This links `storage/app/public` to `public/storage`, making uploaded files servable over HTTP — Laravel keeps uploads outside the web root by default for security.

### 3.2 Add upload routes

```php
Route::get('/upload-form', function () {
    return '
        <form method="POST" action="/upload" enctype="multipart/form-data">
            <input type="hidden" name="_token" value="' . csrf_token() . '">
            <input type="file" name="myfile">
            <button type="submit">Upload</button>
        </form>
    ';
});

Route::post('/upload', function (\Illuminate\Http\Request $request) {
    $path = $request->file('myfile')->store('uploads', 'public');
    return response()->json([
        'message' => 'File uploaded successfully!',
        'path' => $path,
        'url' => asset('storage/' . $path),
    ]);
});
```

**Result confirmed:** Upload via the form (or `curl` with a CSRF token and session cookie) returned JSON with a real file path; the file was verified both on disk (`ls`) and reachable via its public URL (`curl -I` → `200 OK`).

---

## Part 4: Dockerizing the Application

**Architecture chosen:** Nginx (web server) + PHP-FPM (runs Laravel) + MySQL — three separate containers, the production-style pattern rather than Laravel's built-in dev server.

### 4.1 Project structure

```
laravel-demo/
├── compose.yml
├── docker/
│   ├── php/
│   │   └── Dockerfile
│   └── nginx/
│       └── default.conf
└── (rest of the Laravel app)
```

### 4.2 PHP-FPM Dockerfile

```dockerfile
FROM php:8.2-fpm

RUN apt-get update && apt-get install -y \
    libzip-dev zip unzip git curl \
    && docker-php-ext-install pdo pdo_mysql zip

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www
COPY . .
RUN composer install --no-interaction --optimize-autoloader
RUN chown -R www-data:www-data /var/www/storage /var/www/bootstrap/cache

EXPOSE 9000
CMD ["php-fpm"]
```

### 4.3 Nginx config

```nginx
resolver 127.0.0.11 valid=10s;

server {
    listen 80;
    index index.php index.html;
    root /var/www/public;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        set $upstream laravel-php:9000;
        fastcgi_pass $upstream;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

### 4.4 Final `compose.yml` (after all fixes)

```yaml
services:
  laravel-php:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
    container_name: laravel-php
    networks:
      - laravel-net
    volumes:
      - .:/var/www
      - laravel-storage:/var/www/storage/app/public
    environment:
      - DB_CONNECTION=mysql
      - DB_HOST=laravel-db
      - DB_PORT=3306
      - DB_DATABASE=laravel_demo
      - DB_USERNAME=laravel_user
      - DB_PASSWORD=laravel_pass

  laravel-nginx:
    image: nginx:alpine
    container_name: laravel-nginx
    ports:
      - "8000:80"
    volumes:
      - ./docker/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - .:/var/www:ro
      - laravel-storage:/var/www/storage/app/public
    depends_on:
      - laravel-php
    networks:
      - laravel-net

  laravel-db:
    image: mysql:8
    container_name: laravel-db
    environment:
      - MYSQL_ROOT_PASSWORD=rootpass
      - MYSQL_DATABASE=laravel_demo
      - MYSQL_USER=laravel_user
      - MYSQL_PASSWORD=laravel_pass
    volumes:
      - laravel-db-data:/var/lib/mysql
    networks:
      - laravel-net

networks:
  laravel-net:
    driver: bridge

volumes:
  laravel-storage:
  laravel-db-data:
```

### Real problems hit and fixed

**Problem 1 — Port conflict.** `laravel-nginx` failed to start: `address already in use` on port 8000. Cause: the systemd `laravel-dev` service was still running (`stop`/`disable` alone didn't kill an orphaned process). Fixed with `sudo kill <PID>` after finding it via `sudo lsof -i :8000`.

**Problem 2 — Nginx crash on startup.**
```
nginx: [emerg] host not found in upstream "laravel-php"
```
Cause: Nginx resolves upstream hostnames **once, at startup** by default. If `laravel-php` isn't fully DNS-registered yet when Nginx starts, Nginx treats this as fatal and refuses to start entirely — unlike a normal failed request. Fixed by using Nginx's `resolver` directive pointed at Docker's internal DNS (`127.0.0.11`) combined with a `set $upstream` variable, forcing lazy, per-request resolution instead of a one-time startup lookup.

**Problem 3 — Static files returning 403 via PHP instead of Nginx.** Nginx only had the config and the uploads volume mounted — not the actual application files — so it couldn't serve static files directly and fell through to PHP, which returned an error. Fixed by bind-mounting the entire project (`.:/var/www`) into both `laravel-php` and `laravel-nginx`, with the named volume mounted *on top of* just the uploads subfolder.

---

## Part 5: Volume Testing

### 5.1 Confirm storage symlink inside the container

```bash
docker compose exec laravel-php php artisan storage:link
```

### 5.2 Upload through the containerized app

CSRF protection requires the session cookie to be carried along with the token:
```bash
TOKEN=$(curl -s -c ~/cookies.txt http://localhost:8000/upload-form | grep -oP 'value="\K[^"]+' | head -1)
curl -X POST http://localhost:8000/upload \
  -b ~/cookies.txt \
  -F "myfile=@$HOME/clean-test.txt" \
  -H "X-CSRF-TOKEN: $TOKEN"
```

### 5.3 Confirm the file's real location

```bash
docker volume inspect laravel-demo_laravel-storage
```
`Mountpoint`: `/var/lib/docker/volumes/laravel-demo_laravel-storage/_data` — Docker manages this location entirely.

### 5.4 Confirm shared access — Nginx can serve what PHP wrote

```bash
curl -I http://localhost:8000/storage/uploads/<filename>
```
Result: `200 OK`, served directly by Nginx — proving the named volume is genuinely shared between both containers.

---

## Part 6: Data Persistence — Named Volume vs. Bind Mount

### 6.1 Named Volume — survives container destruction

```bash
docker compose stop laravel-php
docker compose rm -f laravel-php
docker compose up -d laravel-php
docker compose exec laravel-php ls -la /var/www/storage/app/public/uploads/
```
**Result:** Uploaded file still present — container recreation doesn't touch the volume.

### 6.2 Named Volume — actually deleting it

```bash
docker compose down
docker volume rm laravel-demo_laravel-storage
docker compose up -d
docker compose exec laravel-php ls -la /var/www/storage/app/public/uploads/
```
**Result:** The uploaded file was genuinely gone. Only a file that had been baked into the Docker image (via `COPY . .` at build time) reappeared — Docker automatically re-seeds a brand-new empty volume with whatever already existed at that path inside the image.

### 6.3 Switching to a Bind Mount for uploads

```bash
mkdir -p ~/laravel-demo/host-uploads
```

In `compose.yml`, changed (in both `laravel-php` and `laravel-nginx`):
```yaml
- laravel-storage:/var/www/storage/app/public
```
to:
```yaml
- ./host-uploads:/var/www/storage/app/public
```

```bash
docker compose down
docker compose up -d
docker compose exec laravel-php php artisan storage:link
```

### Real problem hit: permission denied creating the uploads directory

```
Unable to create a directory at /var/www/storage/app/public/uploads.
```
Cause: the freshly created `host-uploads` folder was owned by `root` with `755` permissions — the container's `www-data` user had no write access. **This never happened with the named volume**, since Docker automatically sets correct ownership when it creates a volume.

**Fix applied:**
```bash
sudo chmod -R 777 ~/laravel-demo/host-uploads
```

### 6.4 Bind Mount — survives container destruction

```bash
docker compose stop laravel-php
docker compose rm -f laravel-php
docker compose up -d laravel-php
ls -la ~/laravel-demo/host-uploads/
```
**Result:** File still present — same persistence behavior as the named volume.

### 6.5 Bind Mount — how deletion actually works

```bash
docker volume ls
```
**Result:** No volume exists for this data at all — because a bind mount isn't part of Docker's volume system. The only way to remove it is a normal filesystem operation:
```bash
rm -rf ~/laravel-demo/host-uploads/*
```

---

## Final Comparison

| Aspect | Named Volume | Bind Mount |
|---|---|---|
| Where the data lives | Hidden, Docker-managed path (found via `docker volume inspect`) | A real folder chosen and created by the user — directly browsable |
| Survives container stop/remove/recreate | Yes | Yes |
| How to destroy the data | `docker volume rm <name>` — a deliberate Docker command | `rm -rf` on the real folder — a normal filesystem operation |
| Initial permissions | Worked immediately — Docker auto-set correct ownership | Failed initially — host folder was root-owned; required a manual `chmod` fix |
| Visibility into contents | Requires `docker exec` or `docker volume inspect` | Plain `ls` on a known path |
| Behavior after full deletion and recreation | Re-seeded from whatever exists in the image at that path | Stays empty — no re-seeding observed |

---

## Conclusion

Both storage types genuinely protect data from a container's lifecycle — stopping, removing, and recreating a container never touches either one. The real difference is about **who manages the data and how it's accessed**:

- **Named volumes** are simpler to get right initially, since Docker handles ownership and location automatically, but the data is hidden behind Docker's own management layer — inspecting, backing up, or deleting it requires Docker-specific commands.
- **Bind mounts** give direct, transparent access to data as ordinary host files, but that transparency comes with responsibility — permissions must be managed manually, as demonstrated by the real failure hit during testing.

This matches standard real-world practice: **named volumes are generally preferred for data a container should fully own** (application uploads, database files), while **bind mounts are best suited for data a human needs direct, ongoing access to** — configuration files, source code during active development, or logs.

---

## Full Command Reference

```bash
# Local setup
sudo apt install -y php8.2 php8.2-cli php8.2-mbstring php8.2-xml php8.2-mysql
composer create-project laravel/laravel laravel-demo
php artisan serve --host=0.0.0.0 --port=8000

# MySQL
sudo apt install -y mysql-server
sudo mysql -e "CREATE DATABASE laravel_demo; CREATE USER 'laravel_user'@'localhost' IDENTIFIED BY 'laravel_pass'; GRANT ALL PRIVILEGES ON laravel_demo.* TO 'laravel_user'@'localhost';"

# Laravel
php artisan migrate
php artisan make:migration create_notes_table
php artisan storage:link

# Docker
docker compose up -d --build
docker compose ps
docker compose logs <service> --tail 30
docker compose exec laravel-php php artisan migrate

# Volume inspection
docker volume ls
docker volume inspect <name>
docker volume rm <name>

# Testing persistence
docker compose stop <service>
docker compose rm -f <service>
docker compose up -d <service>

# Bind mount permission fix
sudo chmod -R 777 <host-folder>
```
