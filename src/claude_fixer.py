"""
Claude API integration for complex code transformations.
Currently handles Spring Security config migration only.
"""

import logging
import re
import shutil
from pathlib import Path

import anthropic
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_java

from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

# --- tree-sitter setup ---

_JAVA_LANGUAGE = Language(tree_sitter_java.language())
_parser = Parser(_JAVA_LANGUAGE)

_SECURITY_CONFIG_QUERY = Query(
    _JAVA_LANGUAGE,
    """
    (class_declaration
      (superclass
        (type_identifier) @superclass
        (#eq? @superclass "WebSecurityConfigurerAdapter")
      )
    ) @class
    """,
)

# --- Claude prompt ---

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


SECURITY_MIGRATION_PROMPT = _load_prompt("security_filterchain.txt")

# --- API client (lazy init) ---

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


# --- Public functions ---


def find_security_configs(project_path: Path) -> list[Path]:
    """
    Find all Java files extending WebSecurityConfigurerAdapter.

    Returns:
        List of file paths containing Security configs.
    """
    project_path = project_path.resolve()
    results: list[Path] = []

    for java_file in project_path.rglob("*.java"):
        try:
            source = java_file.read_bytes()
        except OSError as exc:
            logger.warning("Could not read %s: %s", java_file, exc)
            continue

        tree = _parser.parse(source)
        cursor = QueryCursor(_SECURITY_CONFIG_QUERY)
        captures = cursor.captures(tree.root_node)

        if captures.get("class"):
            results.append(java_file)
            logger.debug("Found Security config: %s", java_file)

    logger.info(
        "Found %d WebSecurityConfigurerAdapter class(es) in %s",
        len(results),
        project_path,
    )
    return results


def _extract_code_from_response(text: str) -> str:
    """Extract Java code from Claude's response, stripping markdown fences."""
    # Try to extract from ```java ... ``` block
    match = re.search(r"```java\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try generic ``` block
    match = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Assume the whole response is code
    return text.strip()


def _validate_java_syntax(code: str) -> bool:
    """Check that code parses as valid Java (no ERROR nodes)."""
    tree = _parser.parse(code.encode("utf-8"))
    return not tree.root_node.has_error


def migrate_security_config(file_path: Path) -> tuple[bool, str, int]:
    """
    Use Claude to migrate a Spring Security config from 2.x to 3.x pattern.

    Returns:
        (success: bool, migrated_code_or_error: str, tokens_used: int)
    """
    file_path = file_path.resolve()
    try:
        original_code = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"Could not read {file_path}: {exc}"
        logger.error(msg)
        return False, msg, 0

    prompt = SECURITY_MIGRATION_PROMPT.replace("{original_code}", original_code)
    client = _get_client()

    logger.info("Calling Claude to migrate: %s", file_path.name)
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        msg = f"Claude API error: {exc}"
        logger.error(msg)
        return False, msg, 0

    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    tokens_total = tokens_in + tokens_out
    logger.info(
        "Claude response: %d input tokens, %d output tokens (%d total)",
        tokens_in,
        tokens_out,
        tokens_total,
    )

    migrated_code = _extract_code_from_response(response.content[0].text)

    if not _validate_java_syntax(migrated_code):
        msg = "Claude-generated code has Java syntax errors"
        logger.error(msg)
        logger.debug("Generated code:\n%s", migrated_code)
        return False, msg, tokens_total

    return True, migrated_code, tokens_total


def write_migrated_file(file_path: Path, new_content: str) -> bool:
    """
    Write migrated code to file with backup.

    Creates a .bak file before overwriting.
    Returns success status.
    """
    file_path = file_path.resolve()
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    try:
        shutil.copy2(file_path, backup_path)
        logger.debug("Backup created: %s", backup_path)
    except OSError as exc:
        logger.error("Failed to create backup for %s: %s", file_path, exc)
        return False

    try:
        file_path.write_text(new_content, encoding="utf-8")
        logger.info("Wrote migrated file: %s", file_path)
        return True
    except OSError as exc:
        logger.error("Failed to write %s: %s", file_path, exc)
        # Attempt to restore backup
        try:
            shutil.copy2(backup_path, file_path)
            logger.info("Restored backup for %s", file_path)
        except OSError:
            logger.error("CRITICAL: Could not restore backup for %s", file_path)
        return False
