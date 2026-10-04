# NewsNow

NewsNow is a Django-based news management platform that enables journalists to create articles and newsletters, editors to review and approve content, and readers to view approved content and manage subscriptions. The application includes role-based access control, publisher and journalist subscriptions, approval workflows, JWT-secured REST APIs, webhook integration, automated testing, Sphinx documentation, MariaDB persistence, and Docker support.

## Table of Contents

- [Features](#features)
- [User Roles](#user-roles)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Local Installation](#local-installation)
- [Environment Variables and Secrets](#environment-variables-and-secrets)
- [MariaDB Setup](#mariadb-setup)
- [Run the Application Locally](#run-the-application-locally)
- [Run Automated Tests](#run-automated-tests)
- [REST API](#rest-api)
- [Sphinx Documentation](#sphinx-documentation)
- [Running with Docker](#running-with-docker)
- [Security](#security)
- [Capstone Submission](#capstone-submission)

## Features

### User Management

- User registration and authentication.
- Reader, Journalist, and Editor roles.
- Role-based access control across web views and API endpoints.

### Article Management

Journalists can:

- Create articles.
- Update their own articles.
- Delete their own articles.
- Submit articles for editorial approval.

Editors can:

- View pending articles.
- Review and approve submitted articles.
- Update articles.
- Delete articles.

Readers can:

- View approved articles.
- Browse content from subscribed publishers and journalists.

### Publisher Management

- Publishers can be associated with editors and journalists.
- Articles can be linked to publishers.
- Readers can subscribe to publishers.

### Subscription Management

Readers can subscribe to:

- Publishers.
- Journalists.

### Newsletter Management

- Journalists can create and manage newsletters.
- Newsletters can contain multiple articles.
- Readers can browse available newsletters.

### Approval Workflow

1. A journalist creates an article.
2. The article is stored as unapproved.
3. An editor reviews the article in the approval queue.
4. The editor approves the article.
5. The approved article becomes visible to readers.
6. Approval notification and webhook behaviour is triggered according to the application configuration.

## User Roles

| Role | Main permissions |
|---|---|
| Reader | View approved articles and newsletters, and manage subscriptions. |
| Journalist | Create and manage the journalist's own articles and newsletters. |
| Editor | Review, approve, update, and delete articles and newsletters as permitted by the application. |

## Technology Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- MariaDB
- Sphinx
- Docker
- Bootstrap
- HTML and CSS

## Project Structure

The repository contains the Django project, application code, templates, static assets, generated Sphinx documentation, Docker configuration, dependency declarations, and submission files.

Key files and directories include:

```text
newsnow/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── capstone.txt
├── manage.py
├── requirements.txt
├── docs/
├── news/
├── newsnow/
├── static/
└── templates/
```

The exact application directories may vary slightly according to the committed project structure.

## Local Installation

The following instructions use Windows PowerShell.

### 1. Clone the Repository

```powershell
git clone https://github.com/goolamh03/newsnow
cd newsnow
```

### 2. Create a Virtual Environment

```powershell
py -m venv .venv
```

### 3. Activate the Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, allow scripts for the current terminal session and activate the environment again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### 4. Upgrade pip and Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create the Local Environment File

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholders with local configuration values. Variable names must match `.env.example` and the Django settings module.

## Environment Variables and Secrets

The `.env.example` file documents the configuration variables required by the application and must contain placeholder values only.

Depending on the committed application configuration, local values may include:

- Django secret key.
- Debug setting.
- Allowed hosts.
- MariaDB database name.
- MariaDB username.
- MariaDB password.
- MariaDB host and port.
- Email or webhook configuration used by the application.

Do not commit:

- `.env`
- Passwords
- Access tokens
- API keys
- Private keys
- Production credentials

The `.gitignore` file must exclude `.env` and virtual-environment folders. Commit `.env.example` only when it contains safe placeholders and no real secrets.

## MariaDB Setup

Log in to MariaDB with an account that can create databases and users, then run:

```sql
CREATE DATABASE newsnow_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER 'newsnow_user'@'localhost'
    IDENTIFIED BY 'your_password';

GRANT ALL PRIVILEGES ON newsnow_db.*
    TO 'newsnow_user'@'localhost';

FLUSH PRIVILEGES;
```

Replace `your_password` with a private local password and update the corresponding values in `.env`. Do not commit the password.

## Run the Application Locally

Apply the database migrations:

```powershell
python manage.py migrate
```

Create an administrator account if required:

```powershell
python manage.py createsuperuser
```

Start the Django development server:

```powershell
python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

Stop the server by pressing `Ctrl+C` in the terminal.

## Run Automated Tests

Run the Django test suite:

```powershell
python manage.py test
```

Generate a terminal coverage report:

```powershell
coverage run manage.py test
coverage report -m
```

Generate and open the HTML coverage report:

```powershell
coverage html
start htmlcov\index.html
```

Run a Python syntax compilation check:

```powershell
python -m compileall .
```

## REST API

The application exposes REST API endpoints for authentication and NewsNow workflows.

### Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/token/` | Obtain JWT access and refresh tokens. |
| POST | `/api/token/refresh/` | Refresh an access token. |

### Articles

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/articles/` | List articles permitted for the authenticated user. |
| POST | `/api/articles/` | Create an article as an authorized journalist. |
| GET | `/api/articles/<id>/` | Retrieve an article. |
| PUT | `/api/articles/<id>/` | Update an article when authorized. |
| DELETE | `/api/articles/<id>/` | Delete an article when authorized. |
| GET | `/api/articles/subscribed/` | Retrieve articles from subscribed sources. |
| POST | `/api/articles/<id>/approve/` | Approve a pending article as an authorized editor. |
| POST | `/api/approved/` | Receive an article-approval webhook payload. |

### JWT Example

Request:

```http
POST /api/token/
Content-Type: application/json
```

```json
{
  "username": "journalist1",
  "password": "your_password"
}
```

Use the returned access token in subsequent protected requests:

```http
Authorization: Bearer <access_token>
```

Do not place real passwords or tokens in the repository.

### Create an Article Example

```http
POST /api/articles/
Authorization: Bearer <journalist_token>
Content-Type: application/json
```

```json
{
  "title": "My First News Article",
  "content": "Breaking news content",
  "publisher": 1
}
```

### Approve an Article Example

```http
POST /api/articles/1/approve/
Authorization: Bearer <editor_token>
```

The exact response fields depend on the current serializers and API implementation.

## Sphinx Documentation

NewsNow uses Sphinx/reStructuredText-compatible docstrings for key modules, classes, functions, models, views, and serializers. Generated documentation is stored in the `docs` directory and is intentionally included in the repository for reviewer access.

### Generate HTML Documentation

If `conf.py` and the source `.rst` files are directly inside `docs`, run:

```powershell
sphinx-build -b html docs docs\_build\html
```

If the Sphinx source files are inside `docs\source`, run instead:

```powershell
sphinx-build -b html docs\source docs\_build\html
```

Use the command matching the repository's actual Sphinx directory structure.

### View Generated Documentation

```powershell
start docs\_build\html\index.html
```

The generated landing page should be located at:

```text
docs/_build/html/index.html
```

## Running with Docker

Make sure Docker is installed and running.

### Build the Docker Image

From the repository root containing the `Dockerfile`, run:

```powershell
docker build -t newsnow .
```

### Run the Docker Container

Use the local environment file so that secrets are not copied into the image:

```powershell
docker run --name newsnow-app --env-file .env -p 8000:8000 newsnow
```

Open the application at:

```text
http://127.0.0.1:8000/
```

The command assumes that the committed Docker configuration starts the application on port `8000`. If the Docker configuration uses another port or startup command, use the values defined in the committed `Dockerfile`.

### View Running Containers

```powershell
docker ps
```

### Stop and Remove the Container

```powershell
docker stop newsnow-app
docker rm newsnow-app
```

### Rebuild After Code or Dependency Changes

```powershell
docker build --no-cache -t newsnow .
```

## Security

- Passwords are processed using Django's configured password-hashing framework and are never stored as plain text.
- Browser-facing forms use Django's CSRF protection.
- Protected views and API endpoints require authentication and role-appropriate authorization.
- `.env` is excluded from version control.
- `.env.example` contains configuration placeholders only.
- Real passwords, tokens, API keys, and production secrets must never be committed.
- Users should replace example credentials with private local values.

## Documentation and Maintainability

- Sphinx/reStructuredText-compatible docstrings document key project components.
- Models, forms, views, serializers, permissions, signals, templates, and static assets are separated according to their responsibilities.
- Generated Sphinx HTML is committed so that reviewers can inspect the documentation.
- `requirements.txt` records the Python dependencies needed to install the project.
- The Docker configuration provides a repeatable application runtime.

## Capstone Submission

The `capstone.txt` file must contain only the public repository link:

```text
https://github.com/goolamh03/newsnow
```

Repository: [NewsNow on GitHub](https://github.com/goolamh03/newsnow)

## License

This project was created as a software engineering capstone submission. No separate open-source licence is asserted unless a licence file is included in the repository.
