"""
Config properties migration: application.properties / application.yml
from Spring Boot 2.x to 3.x.
"""

import logging
from pathlib import Path

from src.claude_fixer import _get_client, _load_prompt, write_migrated_file
from src.config import CLAUDE_MODEL

logger = logging.getLogger(__name__)

_CONFIG_PROMPT_TEMPLATE = _load_prompt("config_properties.txt")

# File names we scan for
_CONFIG_PATTERNS = [
    "application.properties",
    "application.yml",
    "application.yaml",
    "application-*.properties",
    "application-*.yml",
    "application-*.yaml",
]

# Deprecated Boot 2.x property prefixes/keys that signal migration is needed
_DEPRECATED_MARKERS = [
    "spring.redis.",
    "spring.jpa.hibernate.use-new-id-generator-mappings",
    "server.max-http-header-size",
    "spring.elasticsearch.rest.",
    "spring.config.use-legacy-processing",
    "spring.flyway.ignore-future-migrations",
    "management.metrics.export.",
    "spring.security.oauth2.resourceserver.jwt.jws-algorithm=",
    # Hibernate dialect renames (in config values)
    "MySQL5Dialect",
    "MySQL5InnoDBDialect",
    "MySQL8Dialect",
    "PostgreSQL9Dialect",
    "PostgreSQL95Dialect",
    "PostgreSQL10Dialect",
    "Oracle12cDialect",
    "SQLServer2012Dialect",
]


def find_config_files(project_path: Path) -> list[Path]:
    """Find application config files that contain deprecated Boot 2.x properties."""
    project_path = project_path.resolve()
    results: list[Path] = []

    candidates: list[Path] = []
    for pattern in _CONFIG_PATTERNS:
        candidates.extend(project_path.rglob(pattern))

    for cfg in candidates:
        try:
            content = cfg.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read %s: %s", cfg, exc)
            continue

        if any(marker in content for marker in _DEPRECATED_MARKERS):
            results.append(cfg)
            logger.debug("Found config needing migration: %s", cfg)

    logger.info("Found %d config file(s) needing migration in %s", len(results), project_path)
    return results


def _build_prompt(content: str, is_yaml: bool) -> str:
    """Build the Claude prompt for a config file."""
    file_type = "YAML" if is_yaml else "properties"
    return (_CONFIG_PROMPT_TEMPLATE
            .replace("{original_content}", content)
            .replace("{file_type}", file_type))


def migrate_config_file(file_path: Path) -> tuple[bool, str, int]:
    """
    Use Claude to migrate a config file from Boot 2.x to 3.x.

    Returns:
        (success, migrated_content_or_error, tokens_used)
    """
    file_path = file_path.resolve()
    try:
        original_content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"Could not read {file_path}: {exc}"
        logger.error(msg)
        return False, msg, 0

    is_yaml = file_path.suffix in (".yml", ".yaml")
    prompt = _build_prompt(original_content, is_yaml)
    client = _get_client()

    logger.info("Calling Claude to migrate config: %s", file_path.name)
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
    logger.info("Claude config migration: %d tokens", tokens_total)

    migrated = response.content[0].text.strip()
    # Strip markdown fences if present
    if migrated.startswith("```"):
        lines = migrated.split("\n")
        # Remove first and last fence lines
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        migrated = "\n".join(lines)

    return True, migrated, tokens_total
