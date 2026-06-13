from __future__ import annotations

from datetime import date

from typer.testing import CliRunner

from gh_service import _is_in_date_range
from main import app

# ── 날짜 형식 파싱 테스트 ──────────────────────────────────────


def test_valid_date_string_in_range():
    assert (
        _is_in_date_range("2026-06-05T12:00:00Z", date(2026, 6, 1), date(2026, 6, 10))
        is True
    )


def test_invalid_date_string_returns_true():
    assert _is_in_date_range("not-a-date", date(2026, 6, 1), date(2026, 6, 10)) is True


def test_none_date_string_returns_true():
    assert _is_in_date_range(None, date(2026, 6, 1), date(2026, 6, 10)) is True


# ── since 필터 테스트 ──────────────────────────────────────────


def test_before_since_is_excluded():
    assert _is_in_date_range("2026-05-31T00:00:00Z", date(2026, 6, 1), None) is False


def test_on_since_is_included():
    assert _is_in_date_range("2026-06-01T00:00:00Z", date(2026, 6, 1), None) is True


def test_after_since_is_included():
    assert _is_in_date_range("2026-06-05T00:00:00Z", date(2026, 6, 1), None) is True


# ── until 필터 테스트 ──────────────────────────────────────────


def test_after_until_is_excluded():
    assert _is_in_date_range("2026-06-11T00:00:00Z", None, date(2026, 6, 10)) is False


def test_on_until_is_included():
    assert _is_in_date_range("2026-06-10T00:00:00Z", None, date(2026, 6, 10)) is True


def test_before_until_is_included():
    assert _is_in_date_range("2026-06-05T00:00:00Z", None, date(2026, 6, 10)) is True


# ── since + until 범위 테스트 ──────────────────────────────────


def test_both_none_always_included():
    assert _is_in_date_range("2026-01-01T00:00:00Z", None, None) is True


def test_within_range_is_included():
    assert (
        _is_in_date_range("2026-06-05T00:00:00Z", date(2026, 6, 1), date(2026, 6, 10))
        is True
    )


def test_outside_range_before_since_is_excluded():
    assert (
        _is_in_date_range("2026-05-31T00:00:00Z", date(2026, 6, 1), date(2026, 6, 10))
        is False
    )


def test_outside_range_after_until_is_excluded():
    assert (
        _is_in_date_range("2026-06-11T00:00:00Z", date(2026, 6, 1), date(2026, 6, 10))
        is False
    )


# ── CLI 날짜 검증 테스트 ───────────────────────────────────────


def test_invalid_since_format_exits():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "oss2026hnu/reposcore-py",
            "--token",
            "dummy",
            "--since",
            "2026/06/01",
        ],
    )
    assert result.exit_code == 1
    assert "YYYY-MM-DD" in result.output or "YYYY-MM-DD" in (result.stderr or "")


def test_invalid_until_format_exits():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "oss2026hnu/reposcore-py",
            "--token",
            "dummy",
            "--until",
            "06-01-2026",
        ],
    )
    assert result.exit_code == 1


def test_since_after_until_exits():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "oss2026hnu/reposcore-py",
            "--token",
            "dummy",
            "--since",
            "2026-06-10",
            "--until",
            "2026-06-01",
        ],
    )
    assert result.exit_code == 1
