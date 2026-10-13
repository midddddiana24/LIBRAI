"""Public request logs must not expose signed download tickets."""


def test_download_ticket_is_redacted_in_app_log(client, caplog):
    ticket = "private-ticket-value"
    with caplog.at_level("INFO", logger="backend.main"):
        response = client.get(f"/api/v1/reports/public-download/{ticket}")

    assert response.status_code in {401, 403}
    records = [record.getMessage() for record in caplog.records if record.name == "backend.main"]
    assert any("/reports/public-download/{ticket}" in message for message in records)
    assert all(ticket not in message for message in records)
