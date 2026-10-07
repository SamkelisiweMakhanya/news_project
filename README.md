# News Application

A Django news platform built for the HyperionDev capstone brief. It provides role-based publishing, editorial approval, subscriptions, newsletters, a REST API, automated tests, and MariaDB support.

## Roles and workflows

- **Reader:** register/login, browse approved articles and newsletters, subscribe to publishers and journalists, and view a personalised feed.
- **Journalist:** create, view, edit, and delete independent and publisher-associated articles; create and manage newsletters made from their approved articles.
- **Editor:** review and approve pending articles, manage articles/newsletters, create and manage publishers, and link journalists/editors to publishers.

Core workflows are available through normal web pages. Django Admin is retained only as an optional administration tool.

## API

- `POST /api/token/` - obtain a DRF token.
- `GET /api/articles/` - all approved articles for authenticated users.
- `GET /api/articles/subscribed/` - approved articles matching the authenticated reader's subscriptions.
- `GET /api/articles/<id>/` - retrieve an article.
- `POST /api/articles/` - journalists only.
- `PUT/PATCH/DELETE /api/articles/<id>/` - editors or the owning journalist.
- `GET/POST /api/newsletters/` - view or create newsletters according to role.
- `GET/PUT/PATCH/DELETE /api/newsletters/<id>/` - newsletter management.
- `GET/POST /api/publishers/` and `GET/PUT/PATCH/DELETE /api/publishers/<id>/` - publisher management, with creation/changes restricted to editors.
- `POST /api/approved/` - internal approval-audit endpoint used by the approval workflow.

Use the token in requests as `Authorization: Token <token>`.

## Installation

1. Create a virtual environment:

python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

2. Install dependencies:

pip install -r requirements.txt

3. For quick local development, SQLite is the default:

python manage.py migrate
python manage.py runserver

4. To use the required MariaDB database, set:

DB_ENGINE=mysql
DB_NAME=news_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

Also set a secure `DJANGO_SECRET_KEY` and, when needed, `DJANGO_ALLOWED_HOSTS`.

5. Run automated tests:

python manage.py test

## Approval workflow

An editor approves an article from the web review queue. Approval sends email to matching subscribers and POSTs an audit record to `/api/approved/`. The API logging failure is handled defensively so an unavailable audit endpoint does not undo a successful editorial approval.

## Database design

The custom `User` model stores the role and reader subscription relationships. `Publisher` has many editors/journalists through its `members` relationship. `Article` belongs to an author and optionally a publisher. `Newsletter` belongs to a journalist/editor and contains a many-to-many collection of articles.

## Code quality

The project uses Django forms and DRF serializers for validation, role-aware permissions, exception handling around external HTTP calls, descriptive names, modular views/forms, and automated tests for successful and failed requests.

## Project structure

## Project structure

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