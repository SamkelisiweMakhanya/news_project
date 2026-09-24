\# News Application



A Django-based news application that provides a role-based platform for publishing, reviewing, approving, and reading news articles.



\## Features



\* Reader, editor, and journalist user roles.

\* Journalist article creation.

\* Editor article review and approval workflow.

\* Publisher subscriptions.

\* Journalist subscriptions.

\* Newsletter management.

\* REST API endpoints.

\* Email notifications for approved articles.

\* MySQL database support.

\* Sphinx-generated project documentation.



\## Requirements



\* Python 3.13 or compatible Python version.

\* MySQL.

\* Git.

\* Docker (optional).



\## Running Locally with a Virtual Environment



Create and activate a virtual environment:



powershell

python -m venv venv

.\\venv\\Scripts\\Activate.ps1



Install the project dependencies:



powershell

pip install -r requirements.txt



Create the MySQL database required by the application.



The application reads database and Django configuration from environment variables. Do not commit passwords, secret keys, or other credentials to Git.



For local development, set the required environment variables in your PowerShell session. For example:



powershell

$env:DB\_PASSWORD = Read-Host "Enter your MySQL password"

$env:DJANGO\_SECRET\_KEY = Read-Host "Enter your Django secret key"



The database connection can also be configured with:



DB\_NAME

DB\_USER

DB\_PASSWORD

DB\_HOST

DB\_PORT

DJANGO\_ALLOWED\_HOSTS

DJANGO\_SECRET\_KEY



Run the database migrations:



powershell

python manage.py migrate



Run the tests:



powershell

python manage.py test



Start the development server:



powershell

python manage.py runserver



The application will normally be available at:



http://127.0.0.1:8000/



\## Running with Docker



Build the Docker image from the project root:



powershell

docker build -t news\_project .



Run the application container:



powershell

docker run --rm -p 8000:8000 `

&#x20; -e DB\_HOST=host.docker.internal `

&#x20; -e DB\_PASSWORD="$env:DB\_PASSWORD" `

&#x20; news\_project



The container expects the MySQL database to be accessible through the configured database environment variables.



For a different database setup, provide the appropriate values for `DB\_NAME`, `DB\_USER`, `DB\_PASSWORD`, `DB\_HOST`, and `DB\_PORT`.



The Docker configuration is intended to make the application reproducible on another computer with Docker installed.



\## Documentation



Sphinx documentation is included in the repository.



After generating the documentation, the main HTML documentation page is:





Open this file in a web browser to view the generated documentation.



\## Security



Sensitive credentials are not stored in the repository.



Before running the application, obtain the required database credentials and Django secret key from the appropriate administrator or environment. Set them as environment variables rather than placing them directly in source code.



Do not commit `.env` files, passwords, API keys, or other private credentials to GitHub.



\## Project Structure



news\_project/

├── Dockerfile

├── README.md

├── manage.py

├── requirements.txt

├── news/

├── project/

└── docs/

&#x20;   └── \_build/

&#x20;       └── html/



\## Testing



The project's automated tests can be run with:





The application should report that all tests pass before it is considered ready for submission.



