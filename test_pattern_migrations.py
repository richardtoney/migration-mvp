#!/usr/bin/env python3
"""
Test runner for all Claude migration patterns (config, hibernate, security).
Validates each pattern type with pattern-specific checks.

Usage:
    venv/bin/python test_pattern_migrations.py
"""

import json
import logging
import shutil
import sys
import time
from pathlib import Path

from src.claude_fixer import _validate_java_syntax
from src.migration_patterns.config_properties import find_config_files, migrate_config_file
from src.migration_patterns.hibernate_six import find_hibernate_patterns, migrate_hibernate_file
from src.claude_fixer import find_security_configs, migrate_security_config
from src.pattern_validators.security_validator import SecurityMigrationValidator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TEST_BASE = Path(__file__).parent / "test-cases"
METRICS_FILE = Path(__file__).parent / "phase6_metrics.json"


# --- Validators ---

def validate_config_migration(original: str, migrated: str, is_yaml: bool) -> tuple[bool, list[str]]:
    """Validate config property migration."""
    issues: list[str] = []

    # Deprecated keys that should be removed or renamed
    deprecated_checks = [
        ("spring.redis.", "spring.data.redis.", "spring.redis not renamed"),
        ("spring.elasticsearch.rest.", "spring.elasticsearch.", "elasticsearch.rest not renamed"),
        ("server.max-http-header-size", "server.max-http-request-header-size", "max-http-header-size not renamed"),
    ]

    for old_key, new_key, msg in deprecated_checks:
        if old_key in original:
            if is_yaml:
                # For YAML, check the leaf key
                old_leaf = old_key.rstrip(".").split(".")[-1]
                new_leaf = new_key.rstrip(".").split(".")[-1]
                # Simple check: old nested key structure should be gone
                if old_key in migrated and new_key not in migrated:
                    issues.append(msg)
            else:
                if old_key in migrated and new_key not in migrated:
                    issues.append(msg)

    # Properties that should be removed entirely
    remove_checks = [
        "use-new-id-generator-mappings",
        "use-legacy-processing",
    ]
    for key_fragment in remove_checks:
        if key_fragment in original and key_fragment in migrated:
            issues.append(f"'{key_fragment}' should be removed")

    # Deprecated dialects should be updated
    deprecated_dialects = {
        "MySQL5InnoDBDialect": "MySQLDialect",
        "MySQL5Dialect": "MySQLDialect",
        "PostgreSQL95Dialect": "PostgreSQLDialect",
        "PostgreSQL9Dialect": "PostgreSQLDialect",
    }
    for old_dialect, new_dialect in deprecated_dialects.items():
        if old_dialect in original:
            if old_dialect in migrated:
                issues.append(f"Dialect '{old_dialect}' not updated to '{new_dialect}'")

    # Custom properties should be preserved
    if "app." in original or "app:" in original:
        if "app" not in migrated:
            issues.append("Custom app properties lost")

    return len(issues) == 0, issues


def validate_hibernate_migration(original: str, migrated: str) -> tuple[bool, list[str]]:
    """Validate Hibernate 6 migration."""
    issues: list[str] = []

    # @TypeDef/@TypeDefs should be removed
    if "@TypeDef" in migrated:
        issues.append("@TypeDef not removed")
    if "@TypeDefs" in migrated:
        issues.append("@TypeDefs not removed")

    # Old @Type(type=...) should be replaced
    if '@Type(type' in original and '@Type(type' in migrated:
        issues.append("Old @Type(type=...) pattern not migrated")

    # javax → jakarta
    if "javax.persistence" in original:
        if "javax.persistence" in migrated:
            issues.append("javax.persistence not converted to jakarta.persistence")

    # org.hibernate.annotations.Type import should be removed (if @Type usage was removed)
    if "import org.hibernate.annotations.Type;" in migrated and '@Type' not in migrated.split("import")[-1]:
        # Only flag if there are no remaining @Type usages
        pass

    # Entity structure preserved
    if "@Entity" in original and "@Entity" not in migrated:
        issues.append("@Entity annotation lost")

    # Field names preserved
    for field_marker in ["private Long id", "private String name"]:
        if field_marker in original and field_marker not in migrated:
            issues.append(f"Field lost: {field_marker}")

    # Check for new Hibernate 6 annotations
    if '@Type(type = "json")' in original or '@Type(type = "jsonb")' in original:
        if "JdbcTypeCode" not in migrated and "SqlTypes" not in migrated:
            issues.append("JSON @Type not converted to @JdbcTypeCode")

    # Deprecated dialects
    deprecated_dialects = ["MySQL5Dialect", "MySQL5InnoDBDialect", "MySQL8Dialect",
                           "PostgreSQL9Dialect", "PostgreSQL95Dialect"]
    for d in deprecated_dialects:
        if d in original and d in migrated:
            issues.append(f"Deprecated dialect '{d}' not updated")

    return len(issues) == 0, issues


# --- Test runners ---

def test_config_files() -> list[dict]:
    """Test config property migration on all test cases."""
    test_dir = TEST_BASE / "config_properties"
    results = []

    if not test_dir.exists():
        logger.warning("Config test directory not found: %s", test_dir)
        return results

    files = find_config_files(test_dir)
    for f in files:
        logger.info("Testing config: %s", f.name)
        original = f.read_text(encoding="utf-8")
        is_yaml = f.suffix in (".yml", ".yaml")

        start = time.time()
        success, migrated, tokens = migrate_config_file(f)
        elapsed = round(time.time() - start, 2)

        result = {
            "name": f.name,
            "pattern": "config",
            "tokens_used": tokens,
            "success": success,
            "validation_passed": False,
            "time_seconds": elapsed,
            "issues": [],
        }

        if not success:
            result["issues"].append(f"Migration failed: {migrated}")
            logger.error("  FAIL migration: %s", migrated)
        else:
            is_valid, issues = validate_config_migration(original, migrated, is_yaml)
            result["validation_passed"] = is_valid
            result["issues"] = issues
            if is_valid:
                logger.info("  PASS (%d tokens, %.1fs)", tokens, elapsed)
            else:
                logger.error("  FAIL validation:")
                for issue in issues:
                    logger.error("    - %s", issue)
                logger.info("  Migrated content:\n%s", migrated[:500])

        results.append(result)

    return results


def test_hibernate_files() -> list[dict]:
    """Test Hibernate migration on all test cases."""
    test_dir = TEST_BASE / "hibernate_patterns"
    results = []

    if not test_dir.exists():
        logger.warning("Hibernate test directory not found: %s", test_dir)
        return results

    files = find_hibernate_patterns(test_dir)
    for f in files:
        logger.info("Testing hibernate: %s", f.name)
        original = f.read_text(encoding="utf-8")

        start = time.time()
        success, migrated, tokens = migrate_hibernate_file(f)
        elapsed = round(time.time() - start, 2)

        result = {
            "name": f.name,
            "pattern": "hibernate",
            "tokens_used": tokens,
            "success": success,
            "validation_passed": False,
            "syntax_valid": False,
            "time_seconds": elapsed,
            "issues": [],
        }

        if not success:
            result["issues"].append(f"Migration failed: {migrated}")
            logger.error("  FAIL migration: %s", migrated)
        else:
            result["syntax_valid"] = _validate_java_syntax(migrated)
            is_valid, issues = validate_hibernate_migration(original, migrated)
            result["validation_passed"] = is_valid
            result["issues"] = issues
            if is_valid:
                logger.info("  PASS (%d tokens, %.1fs)", tokens, elapsed)
            else:
                logger.error("  FAIL validation:")
                for issue in issues:
                    logger.error("    - %s", issue)
                logger.info("  Migrated code:\n%s", migrated[:500])

        results.append(result)

    return results


def test_security_files() -> list[dict]:
    """Test security migration on all test cases (including new ones)."""
    test_dir = TEST_BASE / "security_configs"
    results = []

    if not test_dir.exists():
        logger.warning("Security test directory not found: %s", test_dir)
        return results

    validator = SecurityMigrationValidator()
    files = sorted(test_dir.glob("*.java"))

    for f in files:
        logger.info("Testing security: %s", f.name)
        original = f.read_text(encoding="utf-8")

        start = time.time()
        success, migrated, tokens = migrate_security_config(f)
        elapsed = round(time.time() - start, 2)

        result = {
            "name": f.name,
            "pattern": "security",
            "tokens_used": tokens,
            "success": success,
            "validation_passed": False,
            "syntax_valid": False,
            "time_seconds": elapsed,
            "issues": [],
        }

        if not success:
            result["issues"].append(f"Migration failed: {migrated}")
            logger.error("  FAIL migration: %s", migrated)
        else:
            result["syntax_valid"] = _validate_java_syntax(migrated)
            is_valid, issues = validator.validate(original, migrated)
            result["validation_passed"] = is_valid
            result["issues"] = issues
            if is_valid:
                logger.info("  PASS (%d tokens, %.1fs)", tokens, elapsed)
            else:
                logger.error("  FAIL validation:")
                for issue in issues:
                    logger.error("    - %s", issue)
                logger.info("  Migrated code:\n%s", migrated[:500])

        results.append(result)

    return results


def main() -> None:
    logger.info("=" * 60)
    logger.info("Phase 6: Pattern Migration Tests")
    logger.info("=" * 60)

    all_results = []

    # Config properties
    logger.info("\n--- Config Properties ---")
    all_results.extend(test_config_files())

    # Hibernate
    logger.info("\n--- Hibernate 6 ---")
    all_results.extend(test_hibernate_files())

    # Security (includes existing + new test cases)
    logger.info("\n--- Security ---")
    all_results.extend(test_security_files())

    # Build metrics
    passed = sum(1 for r in all_results if r["validation_passed"])
    total = len(all_results)
    total_tokens = sum(r["tokens_used"] for r in all_results)

    # Per-pattern summary
    pattern_summary = {}
    for pattern in ("config", "hibernate", "security"):
        pr = [r for r in all_results if r["pattern"] == pattern]
        p_passed = sum(1 for r in pr if r["validation_passed"])
        pattern_summary[pattern] = {
            "total": len(pr),
            "passed": p_passed,
            "failed": len(pr) - p_passed,
            "tokens": sum(r["tokens_used"] for r in pr),
        }

    metrics = {
        "test_cases": [{k: v for k, v in r.items()} for r in all_results],
        "pattern_summary": pattern_summary,
        "summary": {
            "total_tested": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": round(passed / total, 2) if total else 0,
            "total_tokens": total_tokens,
            "avg_tokens_per_file": round(total_tokens / total) if total else 0,
        },
    }

    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    logger.info("Metrics written to %s", METRICS_FILE)

    # Summary
    logger.info("=" * 60)
    logger.info("Results: %d/%d passed", passed, total)
    for pattern, ps in pattern_summary.items():
        logger.info("  %s: %d/%d", pattern, ps["passed"], ps["total"])
    logger.info("=" * 60)
    for r in all_results:
        status = "PASS" if r["validation_passed"] else "FAIL"
        logger.info(
            "  %s  [%s] %s  (%d tokens, %.1fs)",
            status,
            r["pattern"],
            r["name"],
            r["tokens_used"],
            r["time_seconds"],
        )

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
