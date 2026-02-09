"""
Validation tools for migration pipeline.
"""

import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_compilation(project_path: Path) -> tuple[bool, str]:
    """
    Run mvn clean compile and check for errors.

    Args:
        project_path: Path to Maven project root

    Returns:
        (success: bool, maven_output: str)
    """
    project_path = project_path.resolve()
    if not (project_path / "pom.xml").exists():
        msg = f"No pom.xml found at {project_path}"
        logger.error(msg)
        return False, msg

    logger.info("Running Maven compilation: mvn clean compile")

    try:
        result = subprocess.run(
            ["mvn", "clean", "compile"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
    except subprocess.TimeoutExpired:
        msg = "Maven compilation timed out after 300 seconds"
        logger.error(msg)
        return False, msg
    except FileNotFoundError:
        msg = "Maven (mvn) not found on PATH"
        logger.error(msg)
        return False, msg

    combined_output = result.stdout + "\n" + result.stderr
    success = result.returncode == 0

    if success:
        logger.info("Compilation succeeded")
    else:
        errors = parse_compilation_errors(combined_output)
        logger.error("Compilation failed with %d error(s)", len(errors))
        for err in errors[:10]:
            logger.error(
                "  %s:%s — %s", err["file"], err["line"], err["message"]
            )

    return success, combined_output


def parse_compilation_errors(maven_output: str) -> list[dict]:
    """
    Extract compilation errors from Maven output.

    Parses lines like:
        [ERROR] /path/to/File.java:[line,col] error: message

    Returns:
        List of dicts with keys: file, line, column, message
    """
    errors = []
    pattern = re.compile(
        r"\[ERROR\]\s+(.+\.java):\[(\d+),(\d+)\]\s+(.*)"
    )
    for line in maven_output.splitlines():
        match = pattern.search(line)
        if match:
            errors.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "column": int(match.group(3)),
                "message": match.group(4).strip(),
            })
    return errors
