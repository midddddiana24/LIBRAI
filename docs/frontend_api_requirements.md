# LIBRAI Frontend API Requirements

Base URL is configured with `LIBRAI_API_BASE_URL`; examples assume `/api/v1`. JSON errors should contain `detail` or `message`. Standard errors are `400/422` validation, `401` unauthenticated, `403` forbidden, `404` missing resource, `409` policy/state conflict, and `5xx` server failure.

## Authentication

| Method / path | Request | Success response | Used by |
|---|---|---|---|
| `POST /auth/login` | `{username, password}` | `{access_token, user:{id,name,role}}` | Admin login |
| `POST /auth/logout` | none | `{message}` or 204 | Admin logout |

Admin endpoints accept `Authorization: Bearer <token>`.

## QR and kiosk identity

Admin QR presentation uses `GET /users/{id}/qr` and
`GET /book-copies/{id}/qr` to display the current code. Explicit replacement
uses `POST` on the same paths and invalidates the previous code.
These responses include a short-lived `download_url`; the QR dialog opens it
from its Download PNG button so the browser saves a print-ready image.
The admin catalog also uses `POST /books/{id}/copies/qr-sheet` to create a
printable A4 PDF containing labels for all physical copies of that title.

| Method / path | Request | Success response | Used by |
|---|---|---|---|
| `POST /qr/verify-user` | `{token}` | `{id,name,student_id,course,year_level,account_status,current_borrowed_count,borrowing_limit,has_overdue,verification_token}` | Borrow step 1, account |
| `POST /qr/verify-book` | `{token}` | `{id,copy_id,book_id,title,author,category,shelf_location,available,cover_url,verification_token}` | Borrow/return scanner |

Tokens must be opaque secure identifiers. The frontend does not trust or decode embedded personal data.

## Catalog and search

Book creation may include `initial_copy_count` (0-100). The add-book form
defaults this to one so a newly cataloged title is immediately available;
staff can intentionally enter zero for a title awaiting accessioning.

| Method / path | Request | Success response | Used by |
|---|---|---|---|
| `GET /search/books` | Query: `q, category, author, available_only, publication_year` | Array or `{items,total}` of books | Search and catalog lists |
| `GET /books` | Pagination/filter query | Array or `{items,total}` | Admin books |
| `GET /books/{id}` | none | Book detail including keywords, copy counts, shelf and optional `similar_books` | Book detail |
| `POST /books` | ISBN, title, author, publisher, year, category, description, keywords, subjects, shelf, cover reference | Created book | Admin books |
| `PUT /books/{id}` | Editable book fields | Updated book | Admin books |
| `POST /books/{id}/copies` | `{quantity}` or copy payload | Created physical copies with secure QR references | Admin books |
| `POST /books/{id}/archive` | none | Updated status | Admin books |
| `POST /books/{id}/cover` | Multipart JPEG, PNG, or WebP | `{book_id,cover_url}` | Admin book form |

Book list item minimum: `id,title,author,category,cover_url,available_copies,total_copies,shelf_location`.

## Borrow and return

| Method / path | Request | Success response | Used by |
|---|---|---|---|
| `POST /borrowings` | `{user_id,book_copy_id,user_verification_token,book_verification_token}` | `{id,book_title,borrowed_at,due_at,status}` | Confirm borrow |
| `GET /borrowings` | Filters/pagination; user kiosk access includes `verification_token` | Array or `{items,total}` | Account/admin |
| `GET /borrowings/{id}` | none | Full transaction | Admin details |
| `GET /borrowings/active/by-copy/{copy_id}` | Query: `book_verification_token` | `{id,copy_id,book_title,user_name,student_id,due_at,status}` | Return identification |
| `POST /returns` | `{borrowing_id,book_verification_token}` | `{id,book_title,returned_at,return_status}` | Confirm return |
| `GET /returns` | Filters/pagination | Array or `{items,total}` | Admin returns |

The backend alone determines account eligibility, limits, availability, due dates, overdue state, fines, and transaction atomicity. Use `409` with a human-readable message when a business rule rejects a transaction.

## Reservations and users

| Method / path | Request | Success response | Used by |
|---|---|---|---|
| `GET /reservations` | `user_id` or admin filters | Array or `{items,total}` with status, position and expected availability | My/admin reservations |
| `POST /reservations` | `{user_id,book_id,user_verification_token}` | `{id,status,position,expected_available_at?}` | Book details |
| `GET /users` | Filters/pagination | Array or `{items,total}` | Admin users |
| `GET /users/{id}` | none | Profile, status, safe borrowing summary | Account/admin |
| `POST /users` | Student/account fields | Created user | Admin users |
| `PUT /users/{id}` | Editable fields/status | Updated user | Admin users |
| `POST /users/{id}/photo` | Multipart JPEG, PNG, or WebP | Safe user projection with signed `photo_url` | Admin user form |
| `GET /users/photo/{ticket}` | Signed URL | Private WebP image | Admin users / My Account |
| `POST /borrowings/{id}/renew` | `{user_id,user_verification_token}` | Updated receipt with renewal count and due date | My Account |
| `POST /ai/feedback` | `{interaction_id,helpful,user_id?,user_verification_token?}` | Feedback acknowledgement | LIBRAI Assistant |
| `GET /notifications` | `user_id,verification_token` | User-owned in-system notifications | My Account |
| `POST /notifications/{id}/read` | `verification_token` | Updated read state | My Account |

## AI and speech

| Method / path | Request | Success response | Used by |
|---|---|---|---|
| `POST /ai/search` | `{query,user_id?,user_verification_token?}` | `{answer,query,books:[book + why_match?]}` | LIBRAI Assistant |
| `POST /ai/recommend` | `{user_id?,kind,user_verification_token?}` | Array of catalog books | Recommended/popular |
| `POST /speech/transcribe` | Multipart audio or documented media payload | `{text}` | Future microphone adapter |

AI book results must reference only real database records and include availability and shelf location. Gemini keys remain server-side.

## Dashboard, reports, and audit

| Method / path | Request | Success response | Used by |
|---|---|---|---|
| `GET /admin/dashboard` | Optional date range | KPI object plus optional timeseries/category/book/activity series | Admin dashboard |
| `GET /reports` | Type/date filters | Preview rows/summary | Reports preview |
| `POST /reports/export` | `{report_type,start_date?,end_date?,format}` | `{job_id?,download_url?,status}` | Report export |
| `GET /reports/public-download/{ticket}` | Short-lived signed ticket | Generated PDF/CSV/XLSX file | Browser report download |
| `GET /audit-logs` | Filters/pagination | Array or `{items,total}` | Audit logs |

Supported report types: daily/weekly/monthly borrowing, overdue, inventory, most borrowed, popular categories, and user activity. Supported formats: PDF, CSV, XLSX. The backend creates the artifact; the frontend only requests and downloads it.

## File and QR presentation

Book/user detail APIs may expose time-limited `cover_url` and `qr_image_url`. If printable QR sheets are supported, provide a backend export endpoint returning a downloadable PDF. Never return secrets or full personal records inside QR payloads.
