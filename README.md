# Spring Boot Migration MVP

Python CLI tool that combines **OpenRewrite** automated refactoring with **Claude API** intelligent code generation to migrate Spring Boot 2.7 applications to Spring Boot 3.0.

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Run migration (dry-run to preview)
python -m src.mvp_migrator --project-path ./test-projects/spring-petclinic --dry-run

# Run migration (apply changes)
python -m src.mvp_migrator --project-path ./test-projects/spring-petclinic
```

## How It Works

Sequential 4-stage pipeline:

1. **Analyze** — Count Java files, parse pom.xml, estimate complexity
2. **OpenRewrite** — Run Spring Boot 3.0 upgrade recipe via Maven subprocess (javax->jakarta, dependency versions, deprecated APIs)
3. **Claude Pattern Migrations** — Orchestrator coordinates 3 pattern types:
   - **Security** — `WebSecurityConfigurerAdapter` → `SecurityFilterChain` (tree-sitter detection)
   - **Config Properties** — Deprecated Boot 2.x property keys/values → Boot 3.x equivalents
   - **Hibernate 6** — `@Type`/`@TypeDef` annotations, deprecated dialect renames (tree-sitter detection)
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

## Testing

```bash
# Run all pattern migration tests (config + hibernate + security)
venv/bin/python test_pattern_migrations.py

# Run security-only migration tests
venv/bin/python test_security_migrations.py
```

**Pattern test results (8/8 passed):**

| Pattern | Tests | Avg Tokens |
|---|---|---|
| Config Properties | 2/2 | 1,256 |
| Hibernate 6 | 2/2 | 1,634 |
| Security | 4/4 | 974 |

## Architecture

```
src/
├── config.py                # Configuration from .env
├── mvp_migrator.py          # Main pipeline orchestration + CLI
├── openrewrite_runner.py    # OpenRewrite Maven subprocess wrapper
├── claude_fixer.py          # Claude API + tree-sitter for Security configs
├── orchestrator.py          # PatternOrchestrator (coordinates all 3 patterns)
├── validators.py            # Maven compilation validation
├── migration_patterns/
│   ├── config_properties.py # Boot 2.x → 3.x property migration
│   └── hibernate_six.py     # Hibernate 5 → 6 pattern migration
└── pattern_validators/
    └── security_validator.py # Security migration validation (10 checks)

prompts/                     # Claude prompt templates
├── security_filterchain.txt
├── config_properties.txt
└── hibernate_six.txt
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

- Claude handles 3 pattern types (security, config, hibernate); other patterns need manual review
- Compilation validation only (no test execution)
- No rollback — use `git checkout -- . && git clean -fd` to reset
- Sequential processing only
