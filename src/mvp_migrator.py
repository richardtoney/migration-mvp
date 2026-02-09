"""
Main orchestration script.
Sequential pipeline: analyze -> openrewrite -> claude-fix -> validate -> report.
"""

import argparse
import logging
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from src.config import SPRING_BOOT_3_RECIPE, TEST_PROJECT_PATH
from src.openrewrite_runner import run_openrewrite
from src.orchestrator import PatternOrchestrator
from src.validators import parse_compilation_errors, validate_compilation

logger = logging.getLogger(__name__)
_MVN_NS = {"m": "http://maven.apache.org/POM/4.0.0"}


def _make_result(analysis, ow_ok, ow_changes, pattern_results,
                 comp_ok, comp_errors, errors, start):
    """Build the pipeline results dict."""
    totals = pattern_results.get("totals", {"found": 0, "migrated": 0, "tokens": 0})
    return {
        "success": ow_ok and comp_ok and not errors,
        "analysis": analysis,
        "openrewrite_success": ow_ok, "openrewrite_changes": ow_changes,
        "claude_configs_found": totals["found"],
        "claude_configs_migrated": totals["migrated"],
        "claude_total_tokens": totals["tokens"],
        "pattern_results": pattern_results,
        "compilation_success": comp_ok,
        "compilation_errors": comp_errors,
        "errors": errors,
        "duration_seconds": time.time() - start,
    }


def analyze_project(project_path: Path) -> dict:
    """Count files, parse pom.xml, estimate scope."""
    project_path = project_path.resolve()
    total = len(list(project_path.rglob("*.java")))

    project_name, spring_boot_version = "unknown", "unknown"
    pom_path = project_path / "pom.xml"
    if pom_path.exists():
        try:
            root = ET.parse(pom_path).getroot()
            name_el = root.find("m:name", _MVN_NS)
            if name_el is not None and name_el.text:
                project_name = name_el.text.strip()
            parent = root.find("m:parent", _MVN_NS)
            if parent is not None:
                ver_el = parent.find("m:version", _MVN_NS)
                if ver_el is not None and ver_el.text:
                    spring_boot_version = ver_el.text.strip()
        except ET.ParseError as exc:
            logger.warning("Failed to parse pom.xml: %s", exc)

    complexity = "low" if total < 50 else ("medium" if total <= 200 else "high")
    analysis = {
        "total_java_files": total,
        "current_spring_boot_version": spring_boot_version,
        "project_name": project_name,
        "estimated_complexity": complexity,
    }
    logger.info("Project: %s — %d Java files, Boot %s, %s complexity",
                project_name, total, spring_boot_version, complexity)
    return analysis


def run_migration_pipeline(project_path: Path, dry_run: bool = False) -> dict:
    """Execute the complete migration pipeline."""
    start = time.time()
    errors: list[str] = []

    logger.info("=" * 60)
    logger.info("MIGRATION PIPELINE START")
    logger.info("=" * 60)

    # Stage 1: Analyze
    logger.info("--- Stage 1: Project Analysis ---")
    analysis = analyze_project(project_path)

    # Stage 2: OpenRewrite
    logger.info("--- Stage 2: OpenRewrite Migration ---")
    ow_ok, _, ow_changes = run_openrewrite(
        project_path, SPRING_BOOT_3_RECIPE, dry_run=dry_run)
    if not ow_ok:
        errors.append("OpenRewrite execution failed")
        logger.error("OpenRewrite failed — aborting pipeline")
        empty_patterns = {
            p: {"found": 0, "migrated": 0, "tokens": 0, "errors": []}
            for p in ("security", "config", "hibernate")
        }
        empty_patterns["totals"] = {"found": 0, "migrated": 0, "tokens": 0}
        return _make_result(analysis, False, 0, empty_patterns, False, [], errors, start)

    # Stage 3: Claude Pattern Migrations (security + config + hibernate)
    logger.info("--- Stage 3: Claude Pattern Migrations ---")
    orchestrator = PatternOrchestrator()
    pattern_results = orchestrator.run(project_path, dry_run=dry_run)
    # Collect any pattern errors into pipeline errors
    for pattern_name in ("security", "config", "hibernate"):
        for err in pattern_results[pattern_name]["errors"]:
            errors.append(f"[{pattern_name}] {err}")

    # Stage 4: Validate compilation
    logger.info("--- Stage 4: Compilation Validation ---")
    if dry_run:
        logger.info("Dry-run mode: skipping compilation")
        comp_ok, comp_errors = True, []
    else:
        comp_ok, comp_output = validate_compilation(project_path)
        comp_errors = parse_compilation_errors(comp_output) if not comp_ok else []
        if not comp_ok:
            errors.append(f"Compilation failed with {len(comp_errors)} error(s)")

    duration = time.time() - start
    status = "SUCCEEDED" if (ow_ok and comp_ok) else "FAILED"
    logger.info("=" * 60)
    logger.info("MIGRATION PIPELINE %s (%.1fs)", status, duration)
    logger.info("=" * 60)

    return _make_result(analysis, ow_ok, ow_changes, pattern_results,
                        comp_ok, comp_errors, errors, start)


def generate_report(results: dict) -> str:
    """Format migration results as a markdown report."""
    a = results["analysis"]
    status = "SUCCESS" if results["success"] else "FAILED"
    lines = [
        f"# Migration Report — {a['project_name']}", "",
        "## Summary",
        f"- **Status:** {status}",
        f"- **Duration:** {results['duration_seconds']:.1f}s",
        f"- **Errors:** {len(results['errors'])}", "",
        "## Project Analysis",
        f"- **Project:** {a['project_name']}",
        f"- **Spring Boot version:** {a['current_spring_boot_version']}",
        f"- **Java files:** {a['total_java_files']}",
        f"- **Estimated complexity:** {a['estimated_complexity']}", "",
        "## OpenRewrite Results",
        f"- **Executed:** {'Yes' if results['openrewrite_success'] else 'No'}",
        f"- **Files changed:** {results['openrewrite_changes']}", "",
        "## Claude Pattern Migrations",
        f"- **Total files found:** {results['claude_configs_found']}",
        f"- **Total files migrated:** {results['claude_configs_migrated']}",
        f"- **Total tokens used:** {results['claude_total_tokens']}", "",
    ]
    pr = results.get("pattern_results", {})
    for pattern_name, label in [("security", "Security"), ("config", "Config Properties"), ("hibernate", "Hibernate 6")]:
        p = pr.get(pattern_name, {})
        if p:
            lines += [
                f"### {label}",
                f"- Found: {p.get('found', 0)}, Migrated: {p.get('migrated', 0)}, Tokens: {p.get('tokens', 0)}",
                "",
            ]
    lines += [
        "## Compilation Results",
        f"- **Success:** {'Yes' if results['compilation_success'] else 'No'}",
    ]
    if results["compilation_errors"]:
        lines += [f"- **Errors:** {len(results['compilation_errors'])}", "",
                  "### Compilation Errors"]
        for e in results["compilation_errors"]:
            lines.append(f"- `{e['file']}:{e['line']}` — {e['message']}")
    if results["errors"]:
        lines += ["", "## Pipeline Errors"]
        for e in results["errors"]:
            lines.append(f"- {e}")
    lines += ["", "## Next Steps",
              "- [ ] Review OpenRewrite changes for correctness",
              "- [ ] Review Claude-migrated Security configs",
              "- [ ] Run full test suite manually",
              "- [ ] Review deprecated API usage"]
    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Spring Boot 2.7 -> 3.0 Migration Tool")
    parser.add_argument("--project-path", type=Path, default=TEST_PROJECT_PATH,
                        help="Path to Maven project to migrate")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without applying")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    results = run_migration_pipeline(args.project_path, dry_run=args.dry_run)
    print("\n" + generate_report(results))
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
