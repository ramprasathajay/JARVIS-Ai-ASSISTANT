import builtins
from unittest.mock import patch

import foog


def test_confirm_action_accepts_yes_case_insensitive(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda: "yes")
    assert foog.confirm_action("open app") is True

    monkeypatch.setattr(builtins, "input", lambda: "YeS")
    assert foog.confirm_action("open app") is True


def test_open_and_system_commands_accept_yes_flag(monkeypatch):
    monkeypatch.setenv("JARVIS_ENABLE_COMMANDS", "1")

    with patch("foog.confirm_action", return_value=True), patch("foog.webbrowser.open") as browser_open:
        result = foog.open_authorized_application("browser https://example.com yes")
        assert "Opened https://example.com" in result
        browser_open.assert_called_once_with("https://example.com", new=2)

    with patch("foog.confirm_action", return_value=True), patch("foog.subprocess.Popen") as popen:
        result = foog.control_authorized_system("shutdown yes")
        assert "Requested shutdown." == result
        popen.assert_called_once()


def test_open_and_system_commands_do_not_prompt(monkeypatch):
    monkeypatch.setenv("JARVIS_ENABLE_COMMANDS", "1")

    with patch("foog.confirm_action", side_effect=AssertionError("confirmation was requested")):
        with patch("foog.webbrowser.open") as browser_open:
            assert "Opened https://example.com" in foog.open_authorized_application(
                "browser https://example.com"
            )
            browser_open.assert_called_once_with("https://example.com", new=2)

        with patch("foog.subprocess.Popen") as popen:
            assert foog.control_authorized_system("lock") == "Requested lock."
            popen.assert_called_once()


def test_write_command_does_not_prompt(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_ENABLE_COMMANDS", "1")
    monkeypatch.setattr(foog, "WORKSPACE_ROOT", tmp_path)

    with patch("foog.confirm_action", side_effect=AssertionError("confirmation was requested")):
        with patch("foog.subprocess.Popen"):
            result = foog.write_authorized_content("note.txt | hello")

    assert result == "Wrote note.txt and opened it in notepad."
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "hello"


def test_close_command_uses_allowlisted_process(monkeypatch):
    monkeypatch.setenv("JARVIS_ENABLE_COMMANDS", "1")
    monkeypatch.setattr(foog.os, "name", "nt")

    with patch("foog.subprocess.run") as run:
        run.return_value.returncode = 0
        assert foog.close_authorized_application("notepad") == "Closed notepad."
        run.assert_called_once_with(
            ["taskkill", "/IM", "notepad.exe", "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
