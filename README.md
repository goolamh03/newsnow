# NewsNow

A Django-based news management platform that enables journalists to create articles, editors to review and approve content, and readers to consume approved articles. The application includes role-based access control, publisher subscriptions, newsletters, approval workflows, JWT-secured REST APIs, webhook integration, automated testing, and MariaDB persistence.

## 📋 Functional Requirements

The system provides the following core functionality:

### User Management
* **User registration and authentication** workflows.
* **Support for multiple specific user roles:**
  * Reader
  * Journalist
  * Editor
* **Role-based access control (RBAC)** enforcements applied universally throughout the application session layers.

### Article Management
* **Journalists can:**
  * Create articles.
  * Update their own articles.
  * Delete their own articles.
* **Editors can:**
  * View all pending articles in the moderation loop.
  * Approve submitted articles.
  * Update any article database entry.
  * Delete any article database entry.
* **Readers can:**
  * View approved articles only.

### Publisher Management
* Publishers can be associated with journalists.
* Articles are linked explicitly to publishers.
* Readers can subscribe to publishers.

### Subscription Management
* **Readers can subscribe to:**
  * Publishers
  * Journalists
* Readers can retrieve content only from subscribed sources.

### Newsletter Management
* Journalists can create newsletters.
* Newsletters can contain multiple articles.
* Readers can browse available newsletters.

### Approval Workflow
1. Journalist creates an article.
2. Article is stored natively as unapproved.
3. Editor reviews the article in the approval block queue.
4. Editor approves the article.
5. Article becomes instantly visible to readers.

### Notifications and Webhooks
* Subscribers receive notifications when articles are approved.
* Article approval triggers an external webhook payload call.
* Approval events are logged asynchronously in the database.
* Duplicate notifications are safely prevented using the `approval_notified` state boolean flag.

---

## 🛠️ REST API

The application exposes RESTful APIs for handling authentication and application workflows.

### Non-Functional Requirements

#### Performance
* Database queries optimized using:
  * `select_related()` for forward foreign key lookups.
  * `prefetch_related()` for many-to-many and reverse relation lookups.
* Efficient retrieval metrics for processing nested subscription content.

#### Reliability
* **Automated unit tests covering:**
  * Models
  * Permissions Matrix
  * API Views
  * Signals
  * Approval workflow pipelines

#### Maintainability
* Google-style docstrings applied to all modules, view objects, and serialization classes.
* Modular Django application directory architecture.
* Clean separation of concerns between Models, Forms, Views, Serializers, APIs, and Signals.

#### Scalability
* REST APIs fully decoupled to support future front-end framework integrations.
* JWT stateless authentication supports mobile app bundles and SPA clients.

#### Usability
* Bootstrap-based mobile-responsive user navigation layouts.
* Role-based visibility logic hiding functional elements dynamically.

---

## 🔒 Security Requirements

### Authentication
The application leverages stateless **JSON Web Token (JWT)** authentication tokens:
1. **Access Token:** Short-lived token included in headers to verify execution privileges.
2. **Refresh Token:** Long-lived token used to generate fresh access configurations safely.

* **Authentication Token Generation Endpoint:** `POST /api/token/`

### Authorization
Role restrictions are applied to endpoints matching the following access mapping matrix:

| Role | Permitted Route Actions |
| :--- | :--- |
| **Reader** | View approved articles only |
| **Journalist** | Create and manage own articles |
| **Editor** | Approve, inspect, and manage all articles |

### Data Protection
* Passwords stored securely using standard Django Argon2 or BCrypt PBKDF2 hashing.
* CSRF protection middleware enabled for all browser-facing HTML web forms.
* Authentication verification required for all protected backend endpoints.
* Unauthorized or missing tokens return standard `401 Unauthorized` or `403 Forbidden` JSON bodies.

### Webhook Security
* Only verified article approval events trigger webhook requests.
* All outbound execution events are logged with precise timestamps.
* Duplicate webhook calls are safely blocked.

---

### 🚀 Setup on Windows PowerShell

#### Step 1: Clone the Repository

```powershell
git clone https://github.com/goolamh03/newsnow
```

#### Step 2: Navigate into the Project Folder

```powershell
cd newsnow
```

#### Step 3: Create a Virtual Environment

```powershell
py -m venv .venv
```

This creates the `.venv` folder inside the project directory.

#### Step 4: Activate the Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

#### Step 5: Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 6: Create Environment Configuration

```powershell
Copy-Item .env.example .env
```

### Configure MariaDB Core Database Engine
Log into your local MariaDB instance and execute the structural database creation script:

```sql
CREATE DATABASE newsnow_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'newsnow_user'@'localhost'
IDENTIFIED BY 'your_password';

GRANT ALL PRIVILEGES ON newsnow_db.* TO 'newsnow_user'@'localhost';
FLUSH PRIVILEGES;
```

### Run Migrations & Boot Server
```powershell
python manage.py makemigrations news
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🛑 API Endpoints Index

### Authentication
* `POST /api/token/` - Obtain a new pair of JWT Access and Refresh tokens.
* `POST /api/token/refresh/` - Refresh an expired access token using a valid refresh token.

### Articles Management
* `GET /api/articles/` - List accessible articles (filtered by role and approval status).
* `POST /api/articles/` - Create a new article draft (Journalists only).
* `GET /api/articles/<id>/` - Inspect a single article detail record.
* `PUT /api/articles/<id>/` - Modify article contents (Owner or Editor only).
* `DELETE /api/articles/<id>/` - Permanently remove an article record (Owner or Editor only).

### Subscribed Feed Filters
* `GET /api/articles/subscribed/` - Retrieve an aggregated timeline of articles from subscribed profiles.

### Article Moderation Actions
* `POST /api/articles/<id>/approve/` - Approve a pending article submission (Editors only).

### Webhook Endpoint Integrations
* `POST /api/approved/` - Destination receiver endpoint for handling approval automated callback webhooks.

---

## 🧪 Testing APIs with Postman / cURL

* **Local Development Base URL:** `http://127.0.0.1:8000`

### Step 1: Obtain a Valid JWT Token
* **Request:** `POST /api/token/`
* **Payload Body (JSON):**
```json
{
  "username": "journalist1",
  "password": "Test12345!"
}
```
* **Expected Response:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
  "access": "eyJhbGciOiJIUzI1NiIsIn..."
}
```
> 💡 **Usage Note:** Attach the received `access` key parameter as an HTTP header on all subsequent requests: `Authorization: Bearer <access_token>`

### Step 2: Create a New Article Draft
* **Request:** `POST /api/articles/`
* **Headers:** `Authorization: Bearer <journalist_token>`
* **Payload Body (JSON):**
```json
{
  "title": "My First News Article",
  "content": "Breaking news content",
  "publisher": 1
}
```
* **Expected Response:**
```json
{
  "id": 1,
  "title": "My First News Article",
  "approved": false
}
```

### Step 3: Editor Approves the Pending Article
* **Request:** `POST /api/articles/1/approve/`
* **Headers:** `Authorization: Bearer <editor_token>`
* **Expected Response:**
```json
{
  "approved": true
}
```

### Step 4: Verify the Article Update Lifecycle Status
* **Request:** `GET /api/articles/1/`
* **Expected Response:**
```json
{
  "id": 1,
  "title": "My First News Article",
  "approved": true
}
```

### Step 5: Reader Retrieves the Feed Index
* **Request:** `GET /api/articles/`
* **Headers:** `Authorization: Bearer <reader_token>`
* **Expected Response:**
```json
[
  {
    "id": 1,
    "title": "My First News Article",
    "approved": true
  }
]
```

### Step 6: Verify RBAC Security Assertions
If a Reader or Journalist account attempts an unauthorized moderation approval action:
* **Request:** `POST /api/articles/1/approve/`
* **Expected Error Response Code:** `403 Forbidden`

---

## 🚦 Automated Quality Control Checks

### Run Unit Tests
```powershell
python manage.py test
```

### Track Code Test Coverage Metrics
```powershell
coverage run manage.py test
coverage report -m
```

### Generate a Visual HTML Coverage Dashboard Report
```powershell
coverage html
# Opens the reporting chart inside your default system browser window
start htmlcov\index.html
```

### Complete Pre-Deployment Python Syntax Validation Check
```powershell
python -m compileall .
```

---

## 📐 Application Architecture & Design Notes

The core application namespace cleanly isolates components across bounded contexts: **Users, Publishers, Articles, Newsletters, Subscriptions, and Approval Logs**.

