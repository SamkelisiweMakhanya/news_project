# News Application Design

## 1. Functional Requirements

The application allows readers to:

- View approved articles.
- View newsletters.
- Subscribe to publishers.
- Subscribe to independent journalists.
- Retrieve subscribed articles through the REST API.

Editors can:

- View articles and newsletters.
- Update and delete articles and newsletters.
- Review articles awaiting approval.
- Approve articles for publication.

Journalists can:

- Create, view, update, and delete articles.
- Create, view, update, and delete newsletters.
- Publish independent articles.
- Publish content associated with publishers.

When an editor approves an article:

1. The article is marked as approved.
2. Subscribers receive an email notification.
3. A POST request is sent to `/api/approved/`.

## 2. Non-Functional Requirements

The application should provide:

- Readable and maintainable Python code.
- PEP 8 compliant formatting.
- Modular functions and reusable components.
- Defensive validation and exception handling.
- Role-based access control.
- Token-based API authentication.
- Automated tests.
- MariaDB database support.
- Secure handling of authenticated API requests.

## 3. Database Design

### User

Stores authentication information and the user's application role.

Important relationships:

- Reader → many-to-many → Publisher subscriptions.
- Reader → many-to-many → Journalist subscriptions.
- User → one-to-many → Articles authored.
- User → one-to-many → Newsletters authored.

### Publisher

Stores publisher information and has a many-to-many relationship with users who belong to the publisher.

### Article

Stores:

- title
- content
- author
- publisher
- created_at
- approved

An article is either:

- an independent journalist article, or
- publisher-associated content.

### Newsletter

Stores:

- title
- description
- created_at
- author

A newsletter has a many-to-many relationship with Article.

## 4. Normalisation

The database separates users, publishers, articles, and newsletters into independent entities.

Many-to-many relationships are represented using Django's relationship tables rather than duplicated data.

For example:

- Reader subscriptions are stored as relationships rather than repeated publisher data.
- Newsletter articles are stored through a many-to-many relationship.
- Publisher membership is stored as a relationship between users and publishers.

This avoids unnecessary duplication and supports a normalised relational design.

## 5. Roles and Permissions

### Reader

- View articles.
- View newsletters.

### Editor

- View articles and newsletters.
- Update and delete articles and newsletters.
- Approve articles.

### Journalist

- Create, view, update, and delete articles.
- Create, view, update, and delete newsletters.

Django Groups are automatically assigned according to the user's role.

## 6. REST API

Required endpoints:

- `GET /api/articles/`
- `GET /api/articles/subscribed/`
- `GET /api/articles/<id>/`
- `POST /api/articles/`
- `PUT /api/articles/<id>/`
- `DELETE /api/articles/<id>/`
- `GET /api/newsletters/`
- `POST /api/newsletters/`
- `PUT /api/newsletters/<id>/`
- `DELETE /api/newsletters/<id>/`
- `POST /api/approved/`
- `POST /api/token/`

Token authentication is provided by Django REST Framework.

## 7. UI/UX Plan

The application uses a simple responsive layout designed around the three user roles.

### Reader interface

- Article listing.
- Newsletter listing.
- Subscription management.
- Clear article titles and publication information.

### Editor interface

- Review queue.
- Article approval controls.
- Article/newsletter management.

### Journalist interface

- Article creation and editing.
- Newsletter creation and editing.
- Clear publishing status.

The interface uses clear navigation, descriptive buttons, readable typography, validation messages, and access-denied feedback.

## 8. Testing Strategy

Automated Django/DRF tests cover:

- Authentication.
- Reader access.
- Subscription filtering.
- Journalist article creation.
- Journalist article updates.
- Editor article deletion.
- Newsletter permissions.
- Role/group assignment.
- Token authentication.
- Article approval.
- Subscriber email notification.
- Internal approved-article API integration.