"""
OpenRewrite subprocess integration.
Runs OpenRewrite Maven plugin without modifying build files.
"""

import logging
import re
import subprocess
from pathlib import Path

from src.config import OPENREWRITE_VERSION, REWRITE_RECIPE_COORDINATES

logger = logging.getLogger(__name__)


def _build_maven_command(
    recipe: str,
    dry_run: bool = False,
) -> list[str]:
    """Build the Maven command list for OpenRewrite execution."""
    goal = "dryRun" if dry_run else "run"
    plugin = (
        f"org.openrewrite.maven:rewrite-maven-plugin:{OPENREWRITE_VERSION}:{goal}"
    )
    cmd = [
        "mvn",
        "-U",
        plugin,
        f"-Drewrite.recipeArtifactCoordinates={REWRITE_RECIPE_COORDINATES}",
        f"-Drewrite.activeRecipes={recipe}",
    ]
    return cmd


def _parse_change_count(output: str) -> int:
    """Extract the number of changed files from OpenRewrite output.

    Handles two output formats:
      run goal:    'Changes have been made to <path> by:'
      dryRun goal: 'These recipes would make changes to <path>:'
    Each matching line represents one changed file.
    """
    # run goal format: "Changes have been made to <path> by:"
    applied = re.findall(
        r"Changes have been made to (\S+) by:", output
    )
    # dryRun goal format: "These recipes would make changes to <path>:"
    planned = re.findall(
        r"These recipes would make changes to (\S+):", output
    )
    total = len(applied) + len(planned)
    if total > 0:
        return total

    # Fallback: look for summary lines like "Made N changes"
    match = re.search(r"Made (\d+) change", output)
    if match:
        return int(match.group(1))

    return 0


def run_openrewrite(
    project_path: Path,
    recipe: str,
    dry_run: bool = False,
) -> tuple[bool, str, int]:
    """
    Execute OpenRewrite recipe via Maven plugin.

    Args:
        project_path: Path to Maven project root
        recipe: Fully qualified OpenRewrite recipe name
        dry_run: If True, preview changes without applying

    Returns:
        (success: bool, output: str, change_count: int)
    """
    project_path = project_path.resolve()
    if not (project_path / "pom.xml").exists():
        msg = f"No pom.xml found at {project_path}"
        logger.error(msg)
        return False, msg, 0

    cmd = _build_maven_command(recipe, dry_run=dry_run)
    mode = "dry-run" if dry_run else "apply"
    logger.info(
        "Running OpenRewrite %s: recipe=%s, version=%s",
        mode,
        recipe,
        OPENREWRITE_VERSION,
    )
    logger.debug("Command: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )
    except subprocess.TimeoutExpired:
        msg = "OpenRewrite timed out after 600 seconds"
        logger.error(msg)
        return False, msg, 0
    except FileNotFoundError:
        msg = "Maven (mvn) not found on PATH"
        logger.error(msg)
        return False, msg, 0

    combined_output = result.stdout + "\n" + result.stderr
    success = result.returncode == 0

    if success:
        change_count = _parse_change_count(combined_output)
        logger.info(
            "OpenRewrite %s completed successfully: %d change(s) detected",
            mode,
            change_count,
        )
    else:
        change_count = 0
        logger.error(
            "OpenRewrite %s failed (exit code %d)", mode, result.returncode
        )
        logger.error("Output:\n%s", combined_output[-2000:])

    return success, combined_output, change_count
