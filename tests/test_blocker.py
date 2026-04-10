"""Tests for blocker module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from timesaver import blocker


@pytest.fixture
def temp_hosts(tmp_path):
    """Create a temporary hosts file."""
    hosts_file = tmp_path / "hosts"
    hosts_file.write_text(
        """# Host file
127.0.0.1 localhost
255.255.255.255 broadcasthost
::1 localhost
"""
    )
    return hosts_file


def test_read_hosts_file(temp_hosts):
    """Test reading hosts file."""
    content = blocker.read_hosts_file(temp_hosts)
    assert "localhost" in content


def test_write_hosts_file(temp_hosts):
    """Test writing hosts file."""
    blocker.write_hosts_file("test content", temp_hosts)
    assert temp_hosts.read_text() == "test content"


def test_generate_block_entries():
    """Test generating block entries."""
    entries = blocker.generate_block_entries(["twitter.com", "facebook.com"])
    assert blocker.MARKER_START in entries
    assert blocker.MARKER_END in entries
    assert "127.0.0.1 twitter.com" in entries
    assert "127.0.0.1 www.twitter.com" in entries
    assert "127.0.0.1 facebook.com" in entries


def test_generate_block_entries_empty():
    """Test generating block entries with empty list."""
    entries = blocker.generate_block_entries([])
    assert entries == ""


def test_generate_block_entries_with_www():
    """Test that www domains don't get double www."""
    entries = blocker.generate_block_entries(["www.example.com"])
    assert "127.0.0.1 www.example.com" in entries
    # Should not have www.www.example.com
    assert "www.www" not in entries


def test_remove_timesaver_entries(temp_hosts):
    """Test removing TimeSaver entries."""
    content = f"""{temp_hosts.read_text()}
{blocker.MARKER_START}
127.0.0.1 twitter.com
{blocker.MARKER_END}
"""
    result = blocker.remove_timesaver_entries(content)
    assert blocker.MARKER_START not in result
    assert blocker.MARKER_END not in result
    assert "twitter.com" not in result
    assert "localhost" in result


def test_remove_timesaver_entries_no_markers():
    """Test removing entries when no markers exist."""
    content = "127.0.0.1 localhost"
    result = blocker.remove_timesaver_entries(content)
    assert result == content


def test_apply_blocks(temp_hosts):
    """Test applying blocks."""
    blocker.apply_blocks(["twitter.com"], temp_hosts)
    content = temp_hosts.read_text()
    assert blocker.MARKER_START in content
    assert "127.0.0.1 twitter.com" in content
    assert "127.0.0.1 www.twitter.com" in content


def test_apply_blocks_empty(temp_hosts):
    """Test applying empty block list."""
    # First add some blocks
    blocker.apply_blocks(["twitter.com"], temp_hosts)
    # Then apply empty list
    blocker.apply_blocks([], temp_hosts)
    content = temp_hosts.read_text()
    assert blocker.MARKER_START not in content


def test_apply_blocks_replaces_existing(temp_hosts):
    """Test that apply_blocks replaces existing entries."""
    blocker.apply_blocks(["twitter.com"], temp_hosts)
    blocker.apply_blocks(["facebook.com"], temp_hosts)
    content = temp_hosts.read_text()
    assert "twitter.com" not in content
    assert "facebook.com" in content


def test_remove_blocks(temp_hosts):
    """Test removing blocks."""
    blocker.apply_blocks(["twitter.com"], temp_hosts)
    blocker.remove_blocks(temp_hosts)
    content = temp_hosts.read_text()
    assert blocker.MARKER_START not in content
    assert "twitter.com" not in content


def test_flush_dns_cache_success():
    """Test DNS cache flush success."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        result = blocker.flush_dns_cache()
        assert result is True
        mock_run.assert_called_once()


def test_flush_dns_cache_failure():
    """Test DNS cache flush failure."""
    import subprocess

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        result = blocker.flush_dns_cache()
        assert result is False


def test_flush_dns_cache_not_found():
    """Test DNS cache flush when command not found."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = blocker.flush_dns_cache()
        assert result is False


def test_get_current_blocks(temp_hosts):
    """Test getting current blocks."""
    blocker.apply_blocks(["twitter.com", "facebook.com"], temp_hosts)
    blocks = blocker.get_current_blocks(temp_hosts)
    assert "twitter.com" in blocks
    assert "facebook.com" in blocks


def test_get_current_blocks_empty(temp_hosts):
    """Test getting current blocks when none exist."""
    blocks = blocker.get_current_blocks(temp_hosts)
    assert blocks == []


def test_get_current_blocks_file_not_found(tmp_path):
    """Test getting current blocks when file doesn't exist."""
    nonexistent = tmp_path / "nonexistent"
    blocks = blocker.get_current_blocks(nonexistent)
    assert blocks == []


def test_get_current_blocks_removes_www():
    """Test that www prefixes are removed from returned blocks."""
    content = f"""{blocker.MARKER_START}
127.0.0.1 twitter.com
127.0.0.1 www.twitter.com
{blocker.MARKER_END}
"""
    with patch.object(blocker, "read_hosts_file", return_value=content):
        blocks = blocker.get_current_blocks()
        assert blocks == ["twitter.com"]


def test_get_current_blocks_empty_line_in_block():
    """Test handling empty lines within block markers."""
    content = f"""{blocker.MARKER_START}
127.0.0.1 twitter.com

127.0.0.1 facebook.com
{blocker.MARKER_END}
"""
    with patch.object(blocker, "read_hosts_file", return_value=content):
        blocks = blocker.get_current_blocks()
        assert "twitter.com" in blocks
        assert "facebook.com" in blocks


def test_get_current_blocks_malformed_line():
    """Test handling malformed lines (single element) within block markers."""
    content = f"""{blocker.MARKER_START}
127.0.0.1 twitter.com
malformed
127.0.0.1 facebook.com
{blocker.MARKER_END}
"""
    with patch.object(blocker, "read_hosts_file", return_value=content):
        blocks = blocker.get_current_blocks()
        assert "twitter.com" in blocks
        assert "facebook.com" in blocks
        # malformed line should be skipped


def test_write_hosts_file_creates_backup(temp_hosts):
    """Test that write creates a backup file."""
    original_content = temp_hosts.read_text()
    backup_path = temp_hosts.parent / f"{temp_hosts.name}.timesaver.bak"

    blocker.write_hosts_file("new content\n", temp_hosts)

    assert backup_path.exists()
    assert backup_path.read_text() == original_content
    assert temp_hosts.read_text() == "new content\n"


def test_write_hosts_file_atomic(temp_hosts):
    """Test that write is atomic (backup exists after write)."""
    blocker.write_hosts_file("first write\n", temp_hosts)
    blocker.write_hosts_file("second write\n", temp_hosts)

    backup_path = temp_hosts.parent / f"{temp_hosts.name}.timesaver.bak"
    assert backup_path.exists()
    # Backup should have content from before second write
    assert backup_path.read_text() == "first write\n"


def test_has_backup(temp_hosts):
    """Test has_backup function."""
    assert blocker.has_backup(temp_hosts) is False

    # Create a backup
    blocker.write_hosts_file("content\n", temp_hosts)
    assert blocker.has_backup(temp_hosts) is True


def test_get_backup_path(temp_hosts):
    """Test get_backup_path function."""
    backup_path = blocker.get_backup_path(temp_hosts)
    assert backup_path.name == f"{temp_hosts.name}.timesaver.bak"
    assert backup_path.parent == temp_hosts.parent


def test_restore_from_backup(temp_hosts):
    """Test restore_from_backup function."""
    original_content = temp_hosts.read_text()

    # Modify the file (this creates a backup)
    blocker.write_hosts_file("modified content\n", temp_hosts)
    assert temp_hosts.read_text() == "modified content\n"

    # Restore from backup
    result = blocker.restore_from_backup(temp_hosts)
    assert result is True
    assert temp_hosts.read_text() == original_content


def test_restore_from_backup_no_backup(temp_hosts):
    """Test restore_from_backup when no backup exists."""
    result = blocker.restore_from_backup(temp_hosts)
    assert result is False


def test_write_hosts_file_new_file(tmp_path):
    """Test writing to a file that doesn't exist yet."""
    new_hosts = tmp_path / "new_hosts"
    assert not new_hosts.exists()

    blocker.write_hosts_file("new content\n", new_hosts)

    assert new_hosts.exists()
    assert new_hosts.read_text() == "new content\n"
    # No backup should be created for new file
    backup_path = tmp_path / "new_hosts.timesaver.bak"
    assert not backup_path.exists()


def test_write_hosts_file_exception_cleanup(tmp_path):
    """Test that temp file is cleaned up on exception."""
    hosts_file = tmp_path / "hosts"
    hosts_file.write_text("original\n")

    # Make the rename fail by making target a directory
    with patch("pathlib.Path.rename") as mock_rename:
        mock_rename.side_effect = OSError("rename failed")

        with pytest.raises(OSError):
            blocker.write_hosts_file("new content\n", hosts_file)

    # Original file should still exist
    assert hosts_file.read_text() == "original\n"
    # Temp files should be cleaned up
    temp_files = list(tmp_path.glob(".hosts_tmp_*"))
    assert len(temp_files) == 0
