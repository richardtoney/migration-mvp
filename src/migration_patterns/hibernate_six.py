"""
Hibernate 6 migration: @Type/@TypeDef annotations, dialect renames.
Spring Boot 2.x (Hibernate 5) → Spring Boot 3.x (Hibernate 6).
"""

import logging
from pathlib import Path

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_java

from src.claude_fixer import (
    _get_client,
    _extract_code_from_response,
    _load_prompt,
    _validate_java_syntax,
    write_migrated_file,
)
from src.config import CLAUDE_MODEL

logger = logging.getLogger(__name__)

# --- tree-sitter setup ---

_JAVA_LANGUAGE = Language(tree_sitter_java.language())
_parser = Parser(_JAVA_LANGUAGE)

# Detect @Type(type = "...") annotations
_TYPE_ANNOTATION_QUERY = Query(
    _JAVA_LANGUAGE,
    """
    (annotation
      name: (identifier) @ann_name
      (#eq? @ann_name "Type")
      arguments: (annotation_argument_list) @args
    ) @annotation
    """,
)

# Detect @TypeDef / @TypeDefs annotations
_TYPEDEF_ANNOTATION_QUERY = Query(
    _JAVA_LANGUAGE,
    """
    (annotation
      name: (identifier) @ann_name
      (#eq? @ann_name "TypeDef")
    ) @annotation
    """,
)

_TYPEDEFS_ANNOTATION_QUERY = Query(
    _JAVA_LANGUAGE,
    """
    (annotation
      name: (identifier) @ann_name
      (#eq? @ann_name "TypeDefs")
    ) @annotation
    """,
)

# Deprecated Hibernate 5 dialect class names
_DEPRECATED_DIALECTS = [
    "MySQL5Dialect",
    "MySQL5InnoDBDialect",
    "MySQL8Dialect",
    "PostgreSQL9Dialect",
    "PostgreSQL95Dialect",
    "PostgreSQL10Dialect",
    "Oracle12cDialect",
    "SQLServer2012Dialect",
]

_HIBERNATE_PROMPT_TEMPLATE = _load_prompt("hibernate_six.txt")


def find_hibernate_patterns(project_path: Path) -> list[Path]:
    """
    Find Java files with Hibernate 5 patterns needing migration:
    - @Type(type = "...") annotations
    - @TypeDef / @TypeDefs annotations
    - Deprecated dialect references
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
        root = tree.root_node

        # Check for @Type annotations
        cursor = QueryCursor(_TYPE_ANNOTATION_QUERY)
        captures = cursor.captures(root)
        if captures.get("annotation"):
            results.append(java_file)
            logger.debug("Found @Type annotation: %s", java_file)
            continue

        # Check for @TypeDef
        cursor = QueryCursor(_TYPEDEF_ANNOTATION_QUERY)
        captures = cursor.captures(root)
        if captures.get("annotation"):
            results.append(java_file)
            logger.debug("Found @TypeDef annotation: %s", java_file)
            continue

        # Check for @TypeDefs
        cursor = QueryCursor(_TYPEDEFS_ANNOTATION_QUERY)
        captures = cursor.captures(root)
        if captures.get("annotation"):
            results.append(java_file)
            logger.debug("Found @TypeDefs annotation: %s", java_file)
            continue

        # Check for deprecated dialect references in source text
        source_text = source.decode("utf-8", errors="replace")
        if any(dialect in source_text for dialect in _DEPRECATED_DIALECTS):
            results.append(java_file)
            logger.debug("Found deprecated dialect: %s", java_file)

    logger.info(
        "Found %d file(s) with Hibernate 5 patterns in %s",
        len(results),
        project_path,
    )
    return results


def migrate_hibernate_file(file_path: Path) -> tuple[bool, str, int]:
    """
    Use Claude to migrate Hibernate 5 patterns to Hibernate 6.

    Returns:
        (success, migrated_code_or_error, tokens_used)
    """
    file_path = file_path.resolve()
    try:
        original_code = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"Could not read {file_path}: {exc}"
        logger.error(msg)
        return False, msg, 0

    prompt = _HIBERNATE_PROMPT_TEMPLATE.replace("{original_code}", original_code)
    client = _get_client()

    logger.info("Calling Claude to migrate Hibernate patterns: %s", file_path.name)
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        msg = f"Claude API error: {exc}"
        logger.error(msg)
        return False, msg, 0

    tokens_total = response.usage.input_tokens + response.usage.output_tokens
    logger.info("Claude Hibernate migration: %d tokens", tokens_total)

    migrated_code = _extract_code_from_response(response.content[0].text)

    if not _validate_java_syntax(migrated_code):
        msg = "Claude-generated code has Java syntax errors"
        logger.error(msg)
        logger.debug("Generated code:\n%s", migrated_code)
        return False, msg, tokens_total

    return True, migrated_code, tokens_total
