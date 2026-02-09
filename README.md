# Spring Boot Migration MVP

Python CLI tool that combines **OpenRewrite** automated refactoring with **Claude API** intelligent code generation to migrate Spring Boot 2.7 applications to Spring Boot 3.0.

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your ANTHROPIC_API_KEY

# Run migration (dry-run to preview)
python -m src.mvp_migrator --project-path ./test-projects/spring-petclinic --dry-run

# Run migration (apply changes)
python -m src.mvp_migrator --project-path ./test-projects/spring-petclinic
```

## How It Works

Sequential 4-stage pipeline:

1. **Analyze** — Count Java files, parse pom.xml, estimate complexity
2. **OpenRewrite** — Run Spring Boot 3.0 upgrade recipe via Maven subprocess (javax->jakarta, dependency versions, deprecated APIs)
3. **Claude** — Find `WebSecurityConfigurerAdapter` classes via tree-sitter, migrate to `SecurityFilterChain` pattern via Claude API
4. **Validate** — Run `mvn clean compile` to verify migration compiles

## Test Results (spring-petclinic)

| Metric | Value |
|---|---|
| Files analyzed | 35 |
| Files changed (OpenRewrite) | 17 |
| Compilation | SUCCESS |
| Runtime | ~57s |
| Automation rate | 49% (17/35 files) |

## Requirements

- Python 3.11+
- Java 17+ and Maven 3.6+
- Anthropic API key

## Architecture

```
src/
├── config.py              # Configuration from .env
├── openrewrite_runner.py   # OpenRewrite Maven subprocess wrapper
├── claude_fixer.py         # Claude API + tree-sitter for Security configs
├── validators.py           # Maven compilation validation
└── mvp_migrator.py         # Main pipeline orchestration + CLI
```

## Running the Migrated Project

After migration, you can run and test the petclinic interactively:

```bash
cd test-projects/spring-petclinic

# Verify compilation
mvn clean compile

# Run the application
mvn spring-boot:run

# Open in browser: http://localhost:8080
# Press Ctrl+C to stop
```

To reset the test project back to its original Spring Boot 2.7.3 state:

```bash
cd test-projects/spring-petclinic
git checkout -- . && git clean -fd
```

## Known Limitations

- Only handles Spring Security config migration via Claude (other patterns need manual review)
- Compilation validation only (no test execution)
- No rollback — use `git checkout -- . && git clean -fd` to reset
- Sequential processing only
