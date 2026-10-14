"""Exercise the remote-media path without sending records to a provider."""

from io import BytesIO
from pathlib import Path

from PIL import Image

from backend.services import media_service, object_storage


class FakeBody:
    def __init__(self, data: bytes):
        self.data = data

    def read(self):
        return self.data


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, *, Bucket, Key, Body, ContentType):
        assert Bucket == "librai-media"
        self.objects[Key] = (Body, ContentType)

    def get_object(self, *, Bucket, Key):
        assert Bucket == "librai-media"
        content, media_type = self.objects[Key]
        return {"Body": FakeBody(content), "ContentType": media_type}

    def delete_object(self, *, Bucket, Key):
        assert Bucket == "librai-media"
        self.objects.pop(Key, None)


def test_private_object_storage_keeps_media_after_local_files_are_gone(monkeypatch, tmp_path):
    fake = FakeS3()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MEDIA_BUCKET", "librai-media")
    monkeypatch.setattr(object_storage, "_client", lambda: fake)
    monkeypatch.setattr(media_service, "MEDIA_ROOT", Path("generated"))
    image = BytesIO()
    Image.new("RGB", (16, 16), "red").save(image, format="PNG")

    photo = media_service.store_image(image.getvalue(), "image/png", "users", 1)
    assert photo.startswith("private/users/")
    photo_response = object_storage.media_response("generated/" + photo, media_type="image/webp")
    assert photo_response.body.startswith(b"RIFF")
    assert photo_response.headers["content-type"] == "image/webp"

    cover = media_service.store_image(image.getvalue(), "image/png", "covers", 2)
    assert cover.startswith("/files/covers/")
    cover_response = object_storage.media_response("generated" + cover.removeprefix("/files"))
    assert cover_response.body.startswith(b"RIFF")

    # Reports are generated under generated/reports in production.
    report_path = Path("generated/reports/test-object-storage.pdf")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(b"%PDF-test")
    try:
        stored = object_storage.put_file(report_path)
        assert not report_path.exists()
        response = object_storage.media_response(stored, filename="test-object-storage.pdf")
        assert response.body == b"%PDF-test"
        assert "attachment" in response.headers["content-disposition"]
    finally:
        report_path.unlink(missing_ok=True)

    media_service._remove_owned(photo)
    assert "generated/" + photo not in fake.objects
