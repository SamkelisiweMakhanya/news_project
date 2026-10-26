# News Application

A Django news platform developed for the HyperionDev capstone project. It supports role-based publishing, editorial approval, reader subscriptions, newsletters, a REST API, automated tests, and MariaDB.

## Features

- **Reader:** Browse approved articles and newsletters, subscribe to publishers and journalists, and view a personalised feed.
- **Journalist:** Create and manage independent or publisher-associated articles, and create newsletters using approved articles.
- **Editor:** Review and approve publisher-associated articles, manage articles and newsletters, and create publishers with editors and journalists.
- **Email notifications:** Notify relevant subscribers when an article is published.
- **REST API:** Retrieve and manage supported resources using Django REST Framework and token authentication.
- **Automated tests:** Test application behaviour, permissions, and API endpoints.

## Technology

- Python
- Django
- Django REST Framework
- MariaDB
- HTML and CSS

## Installation and Setup

### 1. Clone the Repository

Replace `<repository-url>` with the Git URL for your project repository.

```bash
git clone <repository-url>
cd news_project
```

Run the commands from the directory containing `manage.py`.

### 2. Create and Activate a Virtual Environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, you can use Command Prompt instead:

```bat
venv\Scripts\activate.bat
```

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The project uses `mysqlclient` for MariaDB connectivity and `requests` for HTTP requests. The project settings load `.env` using a custom loader, so `python-dotenv` is not required.

### 4. Install and Configure MariaDB

Install MariaDB Server and ensure the database service is running.

Log in to MariaDB using an account with permission to create databases and users. Run the following SQL statements, replacing the example password with a strong password:

```sql
CREATE DATABASE news_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER 'news_user'@'localhost'
    IDENTIFIED BY 'replace-with-a-strong-password';

GRANT ALL PRIVILEGES ON news_db.*
    TO 'news_user'@'localhost';

FLUSH PRIVILEGES;
```

Keep the database name, username, password, host, and port available for the next step.

### 5. Configure Environment Variables

If the project includes `.env.example`, copy it to `.env` in the project root.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux**

```bash
cp .env.example .env
```

Edit `.env` and configure the values for your environment. For example:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=mysql
DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=replace-with-a-strong-password
DB_HOST=localhost
DB_PORT=3306

DEFAULT_FROM_EMAIL=noreply@news.local
```

Generate a unique, secure Django secret key and replace the example value. Make sure the database password matches the password configured in MariaDB.

**Important security notes:**

- Keep `.env` out of version control.
- Never commit real passwords or production secrets.
- For production, set `DJANGO_DEBUG=False`.
- Configure `DJANGO_ALLOWED_HOSTS` with your actual production domain names.
- Configure an appropriate email backend and HTTPS security settings before deployment.

The environment variable names must match those read by `project/settings.py`.

### 6. Apply Database Migrations

From the project root, run:

```bash
python manage.py check
python manage.py migrate
```

If you make model changes that require new migrations, create and review them before applying them:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create an Administrator

```bash
python manage.py createsuperuser
```

Follow the prompts to create the administrator account.

Public registration creates Reader accounts. Assign Editor and Journalist roles only through a trusted administrative process.

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

Use Django Admin at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) for administrative access.

The Django development server is intended for local development, not production deployment.

### 9. Run the Automated Tests

```bash
python manage.py test
```

The tests use Django's test database. Make sure your database configuration and required dependencies are set up correctly before running them.

## Article Approval and Publication

Independent journalists can publish their own independent articles using the independent publishing workflow. Articles associated with a publisher follow the editor approval workflow.

When an article is published or approved, the application attempts to notify relevant subscribers by email and POST an approval payload to `/api/approved/`. The endpoint validates the payload and returns a response; it does not persist an audit record. If the request fails, the article's publication is not rolled back.

During development, Django's console email backend can display outgoing messages in the terminal instead of delivering them to real recipients. Configure a suitable email backend for your environment if actual email delivery is required.

## REST API

The API uses Django REST Framework. Obtain an authentication token through the token endpoint and include it in subsequent requests.

Example authorization header:

Authorization: Token <your-token>

### Available Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/token/` | Obtain an authentication token |
| `GET` | `/api/articles/` | List approved articles available to the authenticated user |
| `GET` | `/api/articles/subscribed/` | Retrieve articles matching a reader's subscriptions |
| Varies | `/api/articles/<id>/` | Retrieve or manage an article according to permissions |
| Varies | `/api/newsletters/` | List or create newsletters according to permissions |
| Varies | `/api/newsletters/<id>/` | Retrieve or manage a newsletter according to permissions |
| Varies | `/api/publishers/` | List or create publishers according to permissions |
| Varies | `/api/publishers/<id>/` | Retrieve or manage a publisher according to permissions |
| `POST` | `/api/approved/` | Receive and validate an approval payload from the publishing workflow |

Not every method is available to every role. Authentication and role-based permissions apply according to the implementation.

For details about endpoint behaviour, inspect `news/urls.py`, `news/api_views.py`, and `news/serializers.py`.

## Database Design

- **User:** Custom user model with Reader, Editor, and Journalist roles, plus reader subscription relationships.
- **Publisher:** Stores publisher details and staff membership.
- **Article:** Stores the title, content, author, creation time, approval status, and optional publisher.
- **Newsletter:** Stores newsletter details, its author, and its many-to-many relationship with articles.

## Project Structure

news_project/
├── manage.py
├── requirements.txt
├── README.md
├── DESIGN.md
├── news/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   ├── test_web.py
│   ├── templates/
│   └── static/
└── project/
    ├── settings.py
    └── urls.py

## Development Notes

- Use Django forms and Django REST Framework serializers to validate input.
- Keep permission checks on both browser views and API endpoints.
- Keep environment secrets outside version control.
- Run `python manage.py check` and `python manage.py test` after making changes.
- Review changes to database models and create migrations when necessary.