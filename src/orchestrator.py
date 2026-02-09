"""
Pattern orchestrator: coordinates all Claude migration pattern types.
Replaces the single-pattern security migration in the pipeline.
"""

import logging
from pathlib import Path

from src.claude_fixer import (
    find_security_configs,
    migrate_security_config,
    write_migrated_file,
)
from src.migration_patterns.config_properties import (
    find_config_files,
    migrate_config_file,
)
from src.migration_patterns.hibernate_six import (
    find_hibernate_patterns,
    migrate_hibernate_file,
)

logger = logging.getLogger(__name__)


class PatternOrchestrator:
    """Coordinates security, config, and Hibernate migration patterns."""

    def run(self, project_path: Path, dry_run: bool = False) -> dict:
        """
        Run all migration patterns on the project.

        Returns a results dict with per-pattern breakdown:
        {
            "security": {"found": N, "migrated": N, "tokens": N, "errors": [...]},
            "config": {"found": N, "migrated": N, "tokens": N, "errors": [...]},
            "hibernate": {"found": N, "migrated": N, "tokens": N, "errors": [...]},
            "totals": {"found": N, "migrated": N, "tokens": N},
        }
        """
        project_path = project_path.resolve()
        results = {}

        if dry_run:
            logger.info("Dry-run mode: skipping Claude pattern migrations")
            for pattern in ("security", "config", "hibernate"):
                results[pattern] = {"found": 0, "migrated": 0, "tokens": 0, "errors": []}
            results["totals"] = {"found": 0, "migrated": 0, "tokens": 0}
            return results

        # Security
        results["security"] = self._run_security(project_path)

        # Config properties
        results["config"] = self._run_config(project_path)

        # Hibernate
        results["hibernate"] = self._run_hibernate(project_path)

        # Totals
        results["totals"] = {
            "found": sum(results[p]["found"] for p in ("security", "config", "hibernate")),
            "migrated": sum(results[p]["migrated"] for p in ("security", "config", "hibernate")),
            "tokens": sum(results[p]["tokens"] for p in ("security", "config", "hibernate")),
        }

        return results

    def _run_security(self, project_path: Path) -> dict:
        """Run security config migration pattern."""
        result = {"found": 0, "migrated": 0, "tokens": 0, "errors": []}
        try:
            files = find_security_configs(project_path)
            result["found"] = len(files)
            for f in files:
                ok, content, tokens = migrate_security_config(f)
                result["tokens"] += tokens
                if ok and write_migrated_file(f, content):
                    result["migrated"] += 1
                elif ok:
                    result["errors"].append(f"Failed to write: {f.name}")
                else:
                    result["errors"].append(f"Migration failed for {f.name}: {content}")
        except Exception as exc:
            logger.error("Security pattern failed: %s", exc)
            result["errors"].append(f"Security pattern error: {exc}")
        return result

    def _run_config(self, project_path: Path) -> dict:
        """Run config properties migration pattern."""
        result = {"found": 0, "migrated": 0, "tokens": 0, "errors": []}
        try:
            files = find_config_files(project_path)
            result["found"] = len(files)
            for f in files:
                ok, content, tokens = migrate_config_file(f)
                result["tokens"] += tokens
                if ok:
                    # Write the migrated content back
                    try:
                        f.write_text(content, encoding="utf-8")
                        result["migrated"] += 1
                        logger.info("Wrote migrated config: %s", f.name)
                    except OSError as exc:
                        result["errors"].append(f"Failed to write {f.name}: {exc}")
                else:
                    result["errors"].append(f"Migration failed for {f.name}: {content}")
        except Exception as exc:
            logger.error("Config pattern failed: %s", exc)
            result["errors"].append(f"Config pattern error: {exc}")
        return result

    def _run_hibernate(self, project_path: Path) -> dict:
        """Run Hibernate 6 migration pattern."""
        result = {"found": 0, "migrated": 0, "tokens": 0, "errors": []}
        try:
            files = find_hibernate_patterns(project_path)
            result["found"] = len(files)
            for f in files:
                ok, content, tokens = migrate_hibernate_file(f)
                result["tokens"] += tokens
                if ok and write_migrated_file(f, content):
                    result["migrated"] += 1
                elif ok:
                    result["errors"].append(f"Failed to write: {f.name}")
                else:
                    result["errors"].append(f"Migration failed for {f.name}: {content}")
        except Exception as exc:
            logger.error("Hibernate pattern failed: %s", exc)
            result["errors"].append(f"Hibernate pattern error: {exc}")
        return result
