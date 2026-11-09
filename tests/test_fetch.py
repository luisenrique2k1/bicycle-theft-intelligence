import pytest
import requests
from unittest.mock import Mock, patch

from pipeline.fetch import get_latest_available_month, validate_month


def test_get_latest_available_month():
    """Select the newest published crime-data month."""

    mock_response = Mock()
    mock_response.json.return_value = [
        {"date": "2026-07"},
        {"date": "2026-09"},
        {"date": "2026-08"},
    ]

    with patch("pipeline.fetch.requests.get", return_value=mock_response) as mock_get:
        latest = get_latest_available_month()

    assert latest == "2026-09"
    mock_response.raise_for_status.assert_called_once()
    mock_get.assert_called_once()

    import pytest


def test_get_latest_available_month_empty_response():
    """Raise an error when the Police API returns no months."""

    mock_response = Mock()
    mock_response.json.return_value = []

    with patch("pipeline.fetch.requests.get", return_value=mock_response):
        with pytest.raises(
            RuntimeError,
            match="Police API returned no available crime-data months",
        ):
            get_latest_available_month()


def test_get_latest_available_month_http_error():
    """Raise an exception when the Police API returns an HTTP error."""

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("503 Service Unavailable")
    )

    with patch("pipeline.fetch.requests.get", return_value=mock_response):
        with pytest.raises(
            requests.exceptions.HTTPError,
            match="503 Service Unavailable",
        ):
            get_latest_available_month()


def test_validate_month_missing_tiles(tmp_path):
    """Reject ingestion when expected geographical tiles are missing."""

    with patch("pipeline.fetch.RAW_DIR", tmp_path):
        with pytest.raises(
            RuntimeError,
            match="Incomplete ingestion for 2026-09",
        ):
            validate_month("2026-09")


def test_validate_month_success(tmp_path):
    """Accept a month when all 12 geographical tiles contain valid JSON."""
    from pipeline.fetch import TILES

    month_dir = tmp_path / "2026-09"
    month_dir.mkdir()

    for tile in TILES:
        (month_dir / f"{tile}.json").write_text(
            "[]", encoding="utf-8"
        )

    with patch("pipeline.fetch.RAW_DIR", tmp_path):
        validate_month("2026-09")
