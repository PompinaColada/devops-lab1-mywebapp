# mywebapp - Simple Inventory

Лабораторна робота з автоматизованого розгортання веб-сервісу обліку обладнання (Simple Inventory).

## Опис проєкту
Веб-сервіс для обліку ІТ-обладнання (інвентаризація). Стек технологій включає:
* **Backend**: Python 3, FastAPI, Uvicorn
* **Database**: MariaDB / MySQL з асинхронним драйвером `aiomysql` (чисті SQL-запити без ORM)
* **Web Server & Reverse Proxy**: Nginx
* **Process Manager**: Systemd з підтримкою Socket Activation
* **Automation**: Bash-скрипт розгортання для Ubuntu 22.04 LTS

---

## Розрахунок варіанту
* **Номер варіанту**: 26
* Відповідно до вимог варіанту:
  * Веб-застосунок налаштовує з'єднання через CLI-аргументи.
  * Номер варіанту (`26`) автоматично записується скриптом автоматизації у файл `/home/student/gradebook`.
  * Реалізовано Systemd Socket Activation на порті `5200`.

---

## Інструкція локального запуску застосунку

### 1. Підготовка бази даних
Переконайтеся, що MariaDB або MySQL запущено та створено необхідну БД та користувача:
```sql
CREATE DATABASE inventory_db;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON inventory_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Створення віртуального середовища
```bash
python3 -m venv .venv
# Для Linux/macOS:
source .venv/bin/activate
# Для Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 3. Встановлення залежностей
```bash
pip install -r requirements.txt
```

### 4. Виконання міграції бази даних
Запустіть скрипт міграції для створення необхідних таблиць:
```bash
python app/migrate.py --db-host 127.0.0.1 --db-user app_user --db-password app_password --db-name inventory_db
```

### 5. Запуск веб-застосунку
```bash
python app/main.py --port 5200 --db-host 127.0.0.1 --db-user app_user --db-password app_password --db-name inventory_db
```
Застосунок буде доступний за адресою: [http://127.0.0.1:5200](http://127.0.0.1:5200).

---

### Вимоги до віртуальної машини та ОС
- **Базовий образ**: Офіційний образ Ubuntu Server 22.04 LTS (завантажується з офіційного сайту ubuntu.com).
- **Мінімальні ресурси**: 1 CPU, 1-2 GB RAM, 10-15 GB Disk.
- **Особливості встановлення**: Під час встановлення ОС необхідно вибрати опцію встановлення OpenSSH server для забезпечення віддаленого доступу.
- **Вхід у систему (до конфігурації)**: До запуску скрипта автоматизації вхід здійснюється через створеного під час інсталяції користувача `student`.

---

## Інструкція запуску `deploy.sh` на віртуальній машині (Ubuntu 22.04 LTS)

### 1. Клонування або копіювання проєкту
Перенесіть папку з проєктом `mywebapp` на цільову віртуальну машину (наприклад, через `scp` або `git`).

### 2. Запуск скрипту автоматизації
Перейдіть у папку проєкту та запустіть скрипт розгортання від імені суперкористувача `root`:
```bash
cd mywebapp
chmod +x deploy/deploy.sh
sudo ./deploy/deploy.sh
```

### 3. Перевірка статусу сервісів
Після успішного завершення скрипту перевірте стан сокета та Nginx:
```bash
# Перевірка сокета Systemd
systemctl status mywebapp.socket

# Перевірка веб-сервера Nginx
systemctl status nginx
```

### 4. Тестування роботи API

* **Перевірка доступу до списку ендпоінтів** (через Nginx порт 80):
  ```bash
  curl http://localhost/
  ```

* **Перевірка роботи бізнес-логіки (JSON)**:
  ```bash
  # Додавання нового предмету
  curl -X POST -H "Content-Type: application/json" -d '{"name": "Server Dell R740", "quantity": 3}' http://localhost/items
  
  # Отримання списку предметів в JSON
  curl -H "Accept: application/json" http://localhost/items
  
  # Отримання деталей предмета в JSON
  curl -H "Accept: application/json" http://localhost/items/1
  ```

* **Перевірка роботи бізнес-логіки (HTML-таблиця)**:
  ```bash
  # Отримання списку предметів у форматі HTML
  curl -H "Accept: text/html" http://localhost/items
  
  # Отримання деталей предмета у форматі HTML
  curl -H "Accept: text/html" http://localhost/items/1
  ```

* **Перевірка блокування сторонніх шляхів** (має повернути HTTP 403 Forbidden):
  ```bash
  curl http://localhost/health/alive
  curl http://localhost/health/ready
  ```

---

## Запуск за допомогою Docker Compose

Для зручного розгортання всього стеку застосунку (База даних MariaDB, FastAPI веб-додаток та веб-сервер Nginx) використовується Docker Compose.

### 1. Запуск системи
Щоб побудувати образи та запустити всі контейнери у фоновому режимі (detached mode), виконайте команду:
```bash
docker compose up -d --build
```

### 2. Перегляд логів
Для моніторингу роботи сервісів та перегляду логів у реальному часі запустіть:
```bash
docker compose logs -f
```

### 3. Зупинка системи
Щоб зупинити та видалити всі контейнери і створені мережі (дані бази даних при цьому зберігаються завдяки named volume `db_data`), виконайте:
```bash
docker compose down
```
