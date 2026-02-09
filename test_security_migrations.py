#!/usr/bin/env python3
"""
Test runner for Security configuration migrations.
Validates Claude can correctly migrate various Security patterns.

Usage:
    venv/bin/python test_security_migrations.py
"""

import json
import logging
import sys
import time
from pathlib import Path

from src.claude_fixer import migrate_security_config, _validate_java_syntax
from src.pattern_validators.security_validator import SecurityMigrationValidator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TEST_DIR = Path(__file__).parent / "test-cases" / "security_configs"
METRICS_FILE = Path(__file__).parent / "phase5_metrics.json"


def test_single_config(
    test_file: Path, validator: SecurityMigrationValidator
) -> dict:
    """Test migration of a single security config file. Returns metrics dict."""
    logger.info("Testing: %s", test_file.name)

    original_code = test_file.read_text(encoding="utf-8")

    start = time.time()
    success, migrated_code, tokens_used = migrate_security_config(test_file)
    elapsed = round(time.time() - start, 2)

    result = {
        "name": test_file.name,
        "tokens_used": tokens_used,
        "success": success,
        "validation_passed": False,
        "syntax_valid": False,
        "time_seconds": elapsed,
        "issues": [],
        "migrated_code": "",
    }

    if not success:
        result["issues"].append(f"Migration failed: {migrated_code}")
        logger.error("  FAIL migration: %s", migrated_code)
        return result

    result["migrated_code"] = migrated_code
    result["syntax_valid"] = _validate_java_syntax(migrated_code)

    is_valid, issues = validator.validate(original_code, migrated_code)
    result["validation_passed"] = is_valid
    result["issues"] = issues

    if is_valid:
        logger.info("  PASS (%d tokens, %.1fs)", tokens_used, elapsed)
    else:
        logger.error("  FAIL validation:")
        for issue in issues:
            logger.error("    - %s", issue)
        logger.info("  Migrated code:\n%s", migrated_code)

    return result


def main() -> None:
    if not TEST_DIR.exists():
        logger.error("Test directory not found: %s", TEST_DIR)
        sys.exit(1)

    test_files = sorted(TEST_DIR.glob("*.java"))
    if not test_files:
        logger.error("No test files found in %s", TEST_DIR)
        sys.exit(1)

    logger.info("Found %d test files in %s", len(test_files), TEST_DIR)

    validator = SecurityMigrationValidator()
    results = []

    for tf in test_files:
        results.append(test_single_config(tf, validator))

    # Build metrics
    passed = sum(1 for r in results if r["validation_passed"])
    total = len(results)
    total_tokens = sum(r["tokens_used"] for r in results)

    # Strip migrated_code from the JSON output (keep it readable)
    metrics_results = []
    for r in results:
        m = {k: v for k, v in r.items() if k != "migrated_code"}
        metrics_results.append(m)

    metrics = {
        "test_cases": metrics_results,
        "summary": {
            "total_configs_tested": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": round(passed / total, 2) if total else 0,
            "total_tokens": total_tokens,
            "avg_tokens_per_config": round(total_tokens / total) if total else 0,
        },
    }

    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    logger.info("Metrics written to %s", METRICS_FILE)

    # Summary
    logger.info("=" * 60)
    logger.info("Results: %d/%d passed", passed, total)
    logger.info("=" * 60)
    for r in results:
        status = "PASS" if r["validation_passed"] else "FAIL"
        logger.info(
            "  %s  %s  (%d tokens, %.1fs)",
            status,
            r["name"],
            r["tokens_used"],
            r["time_seconds"],
        )

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
