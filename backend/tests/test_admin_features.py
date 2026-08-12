from backend.core.config import settings
from io import BytesIO
from PIL import Image


def test_admin_dashboard_catalog_and_report_export(client,auth_headers,tmp_path,monkeypatch):
    dashboard=client.get("/api/v1/admin/dashboard",headers=auth_headers)
    assert dashboard.status_code==200 and "borrowings_by_day" in dashboard.json()
    assert "unmet_searches" in dashboard.json() and "ai_fallback_rate" in dashboard.json() and "renewals_today" in dashboard.json()
    assert client.get("/api/v1/settings",headers=auth_headers).status_code==200
    assert client.put("/api/v1/settings/BORROWING_LIMIT",headers=auth_headers,json={"value":"invalid"}).status_code==422
    assert client.put("/api/v1/settings/BORROWING_LIMIT",headers=auth_headers,json={"value":"5"}).status_code==200
    category=client.post("/api/v1/categories",headers=auth_headers,json={"name":"Cybersecurity","description":"Security titles"})
    assert category.status_code==201
    book=client.post("/api/v1/books",headers=auth_headers,json={"isbn":"9780000000099","title":"Secure Systems","author":"A. Librarian","category_id":category.json()["id"],"shelf_location":"SEC-010","keywords":["security"],"initial_copy_count":1})
    assert book.status_code==201
    assert "created_at" in book.json()
    assert book.json()["total_copies"]==1 and book.json()["available_copies"]==1
    copies=client.post(f"/api/v1/books/{book.json()['id']}/copies",headers=auth_headers,json={"quantity":2})
    assert copies.status_code==201 and len(copies.json())==2
    qr_sheet=client.post(f"/api/v1/books/{book.json()['id']}/copies/qr-sheet",headers=auth_headers,json={})
    assert qr_sheet.status_code==201 and qr_sheet.json()["copy_count"]==3
    qr_sheet_download=client.get(qr_sheet.json()["download_url"])
    assert qr_sheet_download.status_code==200 and qr_sheet_download.headers["content-type"]=="application/pdf"
    monkeypatch.setattr(settings,"report_directory",tmp_path)
    export=client.post("/api/v1/reports/export",headers=auth_headers,json={"report_type":"inventory","format":"csv"})
    assert export.status_code==201
    download=client.get(export.json()["download_url"])
    assert download.status_code==200 and "Secure Systems" in download.text
    audit=client.get("/api/v1/audit-logs",headers=auth_headers)
    assert audit.status_code==200 and audit.json()["total"]>=3
    sorted_catalog=client.get("/api/v1/search/books?sort=newest")
    assert sorted_catalog.status_code==200 and sorted_catalog.json()["total"]>=2


def test_admin_member_management_and_qr_operations(client, auth_headers):
    users = client.get("/api/v1/users", headers=auth_headers)
    assert users.status_code == 200
    member = users.json()["items"][0]
    assert member["first_name"] == "Test"
    assert member["last_name"] == "Student"
    assert member["email"] == "student@librai.test"
    assert "qr_token" not in member

    updated = client.put(
        f"/api/v1/users/{member['id']}",
        headers=auth_headers,
        json={"course": "BS Computer Science", "status": "SUSPENDED"},
    )
    assert updated.status_code == 200
    assert updated.json()["course"] == "BS Computer Science"
    assert updated.json()["status"] == "suspended"

    # An authenticated administrator can inspect member history without a
    # kiosk verification grant. Public/kiosk requests still require one.
    history = client.get(f"/api/v1/borrowings?user_id={member['id']}", headers=auth_headers)
    assert history.status_code == 200
    assert history.json()["items"] == []

    user_qr = client.post(f"/api/v1/users/{member['id']}/qr", headers=auth_headers)
    assert user_qr.status_code == 200
    assert user_qr.json()["qr_image"].startswith("data:image/png;base64,")
    existing_user_qr = client.get(f"/api/v1/users/{member['id']}/qr", headers=auth_headers)
    assert existing_user_qr.status_code == 200
    user_download = client.get(f"/api/v1{existing_user_qr.json()['download_url']}")
    assert user_download.status_code == 200
    assert user_download.headers["content-type"] == "image/png"
    assert "attachment;" in user_download.headers["content-disposition"]

    books = client.get("/api/v1/books", headers=auth_headers).json()["items"]
    copies = client.get(f"/api/v1/books/{books[0]['id']}/copies", headers=auth_headers).json()
    copy_qr = client.post(f"/api/v1/book-copies/{copies[0]['id']}/qr", headers=auth_headers)
    assert copy_qr.status_code == 200
    assert copy_qr.json()["qr_image"].startswith("data:image/png;base64,")
    existing_copy_qr = client.get(f"/api/v1/book-copies/{copies[0]['id']}/qr", headers=auth_headers)
    assert existing_copy_qr.status_code == 200
    copy_download = client.get(f"/api/v1{existing_copy_qr.json()['download_url']}")
    assert copy_download.status_code == 200
    assert copy_download.headers["content-type"] == "image/png"


def test_book_cover_and_private_user_photo_uploads(client, auth_headers, tmp_path, monkeypatch):
    from backend.services import media_service

    monkeypatch.setattr(media_service, "MEDIA_ROOT", tmp_path)
    image_buffer = BytesIO()
    Image.new("RGB", (640, 800), "#1A3C5E").save(image_buffer, format="PNG")
    image_bytes = image_buffer.getvalue()

    book = client.get("/api/v1/books").json()["items"][0]
    cover = client.post(
        f"/api/v1/books/{book['id']}/cover",
        headers=auth_headers,
        files={"file": ("cover.png", image_bytes, "image/png")},
    )
    assert cover.status_code == 200
    assert cover.json()["cover_url"].endswith(".webp")
    assert list((tmp_path / "covers").glob("*.webp"))

    user = client.get("/api/v1/users", headers=auth_headers).json()["items"][0]
    photo = client.post(
        f"/api/v1/users/{user['id']}/photo",
        headers=auth_headers,
        files={"file": ("student.png", image_bytes, "image/png")},
    )
    assert photo.status_code == 200
    assert photo.json()["photo_url"].startswith("/api/v1/users/photo/")
    private_photo = client.get(photo.json()["photo_url"])
    assert private_photo.status_code == 200
    assert private_photo.headers["content-type"] == "image/webp"

    rejected = client.post(
        f"/api/v1/users/{user['id']}/photo",
        headers=auth_headers,
        files={"file": ("fake.png", b"not-an-image", "image/png")},
    )
    assert rejected.status_code == 422


def test_private_generated_files_and_circulation_states_are_protected(client, auth_headers, tmp_path):
    secret_report = tmp_path / "secret.pdf"
    secret_report.write_bytes(b"private")
    # The broad /files mount was removed: reports and QR sheets are only
    # downloadable through short-lived signed endpoints.
    assert client.get("/files/reports/secret.pdf").status_code == 404

    book = client.get("/api/v1/books", headers=auth_headers).json()["items"][0]
    copy = client.get(f"/api/v1/books/{book['id']}/copies", headers=auth_headers).json()[0]
    manually_borrowed = client.put(
        f"/api/v1/book-copies/{copy['id']}",
        headers=auth_headers,
        json={"status": "BORROWED"},
    )
    assert manually_borrowed.status_code == 409


def test_settings_bulk_update_is_atomic(client, auth_headers):
    updated = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={"BORROWING_LIMIT": "4", "RESERVATION_HOLD_DAYS": "3"},
    )
    assert updated.status_code == 200
    assert updated.json()["BORROWING_LIMIT"] == "4"
    assert updated.json()["RESERVATION_HOLD_DAYS"] == "3"

    rejected = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={"BORROWING_LIMIT": "7", "RESERVATION_HOLD_DAYS": "invalid"},
    )
    assert rejected.status_code == 422
    current = client.get("/api/v1/settings", headers=auth_headers).json()
    assert current["BORROWING_LIMIT"] == "4"


def test_catalog_csv_round_trip_and_audit_filters(client, auth_headers):
    csv_body = "isbn,title,author,publisher,publication_year,category,shelf_location,description,keywords,subjects,copies\n9780000000777,Imported Systems,Test Author,Test Press,2024,Technology,T-010,Imported title,python|systems,computing|systems,2\n"
    imported = client.post("/api/v1/books/import.csv", headers=auth_headers, files={"file": ("catalog.csv", csv_body.encode(), "text/csv")})
    assert imported.status_code == 200
    assert imported.json()["imported"] == 1

    exported = client.get("/api/v1/books/export.csv", headers=auth_headers)
    assert exported.status_code == 200
    assert "Imported Systems" in exported.text
    assert "text/csv" in exported.headers["content-type"]

    filtered = client.get("/api/v1/audit-logs?actor_type=ADMIN", headers=auth_headers)
    assert filtered.status_code == 200
    assert all(row["actor_type"] == "ADMIN" for row in filtered.json()["items"])
    audit_csv = client.get("/api/v1/audit-logs/export.csv?actor_type=ADMIN", headers=auth_headers)
    assert audit_csv.status_code == 200
    assert "BOOKS_IMPORTED" in audit_csv.text
