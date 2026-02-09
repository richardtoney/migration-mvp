# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spring Boot 2.7 → 3.0 migration tool. Python CLI that combines OpenRewrite (automated refactoring via Maven subprocess) with Claude API (intelligent code generation) in a 4-stage pipeline: Analyze → OpenRewrite → Claude Pattern Migrations → Compile Validation.

## Commands

```bash
# Run full migration pipeline
venv/bin/python -m src.mvp_migrator --project-path ./test-projects/spring-petclinic

# Dry-run (preview without applying)
venv/bin/python -m src.mvp_migrator --project-path ./test-projects/spring-petclinic --dry-run

# Run all pattern migration tests (config + hibernate + security)
venv/bin/python test_pattern_migrations.py

# Run security-only migration tests
venv/bin/python test_security_migrations.py

# Reset test project before re-running
cd test-projects/spring-petclinic && git checkout -- . && git clean -fd
```

## Architecture

**Pipeline (mvp_migrator.py):**
1. `analyze_project()` — count Java files, parse pom.xml, estimate complexity
2. `run_openrewrite()` — Maven subprocess for automated refactoring (javax→jakarta, versions, deprecated APIs)
3. `PatternOrchestrator().run()` — coordinates 3 Claude migration patterns with per-pattern error isolation
4. `validate_compilation()` — `mvn clean compile` to verify success

**Pattern Orchestrator (orchestrator.py)** delegates to:
- **Security** (`claude_fixer.py`) — tree-sitter detects `WebSecurityConfigurerAdapter`, Claude migrates to `SecurityFilterChain`
- **Config** (`migration_patterns/config_properties.py`) — detects deprecated Boot 2.x property keys, Claude migrates
- **Hibernate** (`migration_patterns/hibernate_six.py`) — tree-sitter detects `@Type`/`@TypeDef` annotations + deprecated dialects, Claude migrates

**Prompt templates** live in `prompts/` and are loaded via `_load_prompt()` in `claude_fixer.py`.

**Test cases** in `test-cases/` organized by pattern type (security_configs/, config_properties/, hibernate_patterns/).

## Critical Implementation Details

- **Prompt template substitution:** Always use `.replace("{placeholder}", value)`, never `.format()`. Java code contains `{}` (generics like `Map<String, Object>`) which breaks Python's format().
- **tree-sitter 0.25 API:** Use `Query(lang, pattern)` constructor (not `lang.query()`). Use `QueryCursor(query)` then `cursor.captures(node)` which returns `dict[str, list[Node]]`.
- **OpenRewrite 6.x dry-run:** Must use separate `dryRun` Maven goal, NOT `-Drewrite.dryRun=true` flag (the flag silently applies changes).
- **Claude API:** All migrations use `temperature=0.0`, `max_tokens=4000`. Lazy-initialized singleton client via `_get_client()`.
- **Shared infrastructure:** Pattern modules reuse `_get_client()`, `_extract_code_from_response()`, `_validate_java_syntax()`, and `write_migrated_file()` from `claude_fixer.py`.

## Environment

- Python 3.11+ in `venv/`, Java 17+, Maven 3.6+
- `ANTHROPIC_API_KEY` required in `.env` (validated on import of `src.config`)
- Test project: spring-petclinic at commit `9ecdc111` (Boot 2.7.3, 35 Java files)
