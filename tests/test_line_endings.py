"""Every text file in the repository ends its lines with LF, and .gitattributes keeps it that way.

A file whose line endings flip, CRLF to LF or back, turns every one of its lines into a diff and
hides the change that was meant. Eight files ended their lines with CRLF until 2.26.1.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = {
    ".cfg",
    ".conf",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
# Not the repository's own files: dependencies, builds, caches and local output.
SKIP = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "output",
    "venv",
}


def _text_files():
    for path in ROOT.rglob("*"):
        parts = set(path.relative_to(ROOT).parts)
        if path.is_file() and path.suffix in TEXT and not parts & SKIP:
            yield path


def test_every_text_file_ends_its_lines_with_lf():
    crlf = [
        str(path.relative_to(ROOT))
        for path in _text_files()
        if b"\r\n" in path.read_bytes()
    ]
    assert crlf == []


def test_git_stores_and_checks_out_text_as_lf():
    rules = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "* text=auto eol=lf" in rules
