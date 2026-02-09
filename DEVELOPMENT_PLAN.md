# Development Plan - Spring Boot Migration MVP

## Overview

This plan breaks the MVP into 4 sequential phases. Each phase must be completed and validated before proceeding to the next. Total estimated time: 6 hours of Claude Code development.

**Phase gates:** After each phase, STOP and wait for explicit approval before proceeding.

---

## Phase 1: Environment Setup & OpenRewrite Integration
**Goal:** Claude Code can successfully run OpenRewrite against spring-petclinic via subprocess  
**Estimated time:** 60-90 minutes

### Tasks

#### 1.1 Create Project Structure
```bash
# Create all necessary files and directories
src/__init__.py           # Empty file for package
src/config.py            # Configuration module
src/openrewrite_runner.py # OpenRewrite integration
requirements.txt         # Already exists
README.md               # Project overview
```

#### 1.2 Implement config.py
**Requirements:**
- Load environment variables from .env using python-dotenv
- Provide typed access to all configuration values
- Validate that required values are present
- Use pathlib.Path for all path variables

**Expected content:**
```python
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')

# Project paths
TEST_PROJECT_PATH = Path(os.getenv('TEST_PROJECT_PATH', './test-projects/spring-petclinic'))

# OpenRewrite configuration
OPENREWRITE_VERSION = os.getenv('OPENREWRITE_VERSION', '6.28.0')
SPRING_BOOT_3_RECIPE = 'org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Validation
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment")
```

#### 1.3 Implement openrewrite_runner.py
**Requirements:**
- Function to run OpenRewrite via subprocess
- Support both dry-run and apply modes
- Capture stdout and stderr
- Parse output to determine success
- Extract count of changes made
- Proper error handling and logging

**Function signature:**
```python
def run_openrewrite(
    project_path: Path,
    recipe: str,
    dry_run: bool = False
) -> tuple[bool, str, int]:
    """
    Run OpenRewrite Maven plugin against a project.
    
    Args:
        project_path: Path to Maven project root
        recipe: Fully qualified OpenRewrite recipe name
        dry_run: If True, preview changes without applying
        
    Returns:
        (success: bool, output: str, change_count: int)
    """
```

**Implementation notes:**
- Use `subprocess.run()` with `capture_output=True`
- Build Maven command as list (not shell string)
- OpenRewrite 6.x uses separate Maven goals: `run` (apply) and `dryRun` (preview)
- Command structure:
  ```bash
  # Apply mode:
  mvn -U org.openrewrite.maven:rewrite-maven-plugin:{version}:run
      -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE
      -Drewrite.activeRecipes={recipe}

  # Dry-run mode (separate goal, NOT a -D flag):
  mvn -U org.openrewrite.maven:rewrite-maven-plugin:{version}:dryRun
      -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE
      -Drewrite.activeRecipes={recipe}
  ```
- Parse output for change indicators (format differs by goal):
  - `run` goal: `"Changes have been made to <path> by:"`
  - `dryRun` goal: `"These recipes would make changes to <path>:"`
- Extract change count by counting matched file lines

#### 1.4 Create README.md
Basic project documentation with:
- Project purpose
- Setup instructions
- Usage example
- Requirements

### Validation Steps

**1. Verify config loads:**
```bash
python -c "from src.config import ANTHROPIC_API_KEY, TEST_PROJECT_PATH; print(f'API key: {ANTHROPIC_API_KEY[:10]}..., Project: {TEST_PROJECT_PATH}')"
# Should print API key prefix and project path
```

**2. Test OpenRewrite dry-run:**
```bash
python -c "
from src.openrewrite_runner import run_openrewrite
from src.config import TEST_PROJECT_PATH, SPRING_BOOT_3_RECIPE
success, output, changes = run_openrewrite(TEST_PROJECT_PATH, SPRING_BOOT_3_RECIPE, dry_run=True)
print(f'Success: {success}, Changes: {changes}')
print(output[:500])
"
# Should show success=True and changes>0
```

**3. Check output quality:**
- Verify Maven output is captured in the output string
- Verify change count is extracted
- Verify no exceptions are raised

### Phase 1 Complete When:
- [x] All modules created with proper imports
- [x] config.py loads environment variables successfully
- [x] openrewrite_runner.py executes Maven command
- [x] Dry-run shows planned changes without error
- [x] Output parsing extracts success status and change count

---

## Phase 2: Basic Orchestration Pipeline
**Goal:** End-to-end pipeline runs with stub implementations for Claude integration  
**Estimated time:** 90 minutes

### Tasks

#### 2.1 Implement validators.py
**Requirements:**
- Function to validate Maven compilation
- Parse Maven output to extract errors
- Return structured error information

**Function signatures:**
```python
def validate_compilation(project_path: Path) -> tuple[bool, str]:
    """
    Run mvn clean compile and check for errors.
    
    Returns:
        (success: bool, maven_output: str)
    """

def parse_compilation_errors(maven_output: str) -> list[dict]:
    """
    Extract compilation errors from Maven output.
    
    Returns:
        List of dicts with keys: file, line, column, message
    """
```

#### 2.2 Implement mvp_migrator.py - Analysis Phase
**Requirements:**
- Count Java files in project
- Parse pom.xml to extract current Spring Boot version
- Estimate migration scope
- Return structured analysis results

**Function signature:**
```python
def analyze_project(project_path: Path) -> dict:
    """
    Analyze project structure and scope.
    
    Returns:
        {
            'total_java_files': int,
            'current_spring_boot_version': str,
            'project_name': str,
            'estimated_complexity': str  # 'low', 'medium', 'high'
        }
    """
```

**Implementation notes:**
- Use pathlib to count .java files: `len(list(project_path.rglob('*.java')))`
- Parse pom.xml with xml.etree.ElementTree
- Handle Maven namespace in XML parsing
- Complexity estimation: <50 files=low, 50-200=medium, >200=high

#### 2.3 Implement mvp_migrator.py - Main Pipeline
**Requirements:**
- Sequential execution: analyze → openrewrite → validate → report
- Structured logging at each stage
- Error handling with graceful degradation
- Return comprehensive results dictionary

**Function signature:**
```python
def run_migration_pipeline(project_path: Path) -> dict:
    """
    Execute the complete migration pipeline.
    
    Returns:
        {
            'success': bool,
            'analysis': dict,
            'openrewrite_changes': int,
            'compilation_success': bool,
            'errors': list[str],
            'duration_seconds': float
        }
    """
```

**Pipeline stages:**
1. Log start with timestamp
2. Run analyze_project()
3. Run run_openrewrite() in APPLY mode (not dry-run)
4. Run validate_compilation()
5. Log results
6. Return structured results

#### 2.4 Implement Report Generation
**Function signature:**
```python
def generate_report(results: dict) -> str:
    """
    Format results as markdown report.
    
    Returns:
        Markdown-formatted string
    """
```

**Report sections:**
- Migration Summary (success/failure, duration)
- Project Analysis (file counts, versions)
- OpenRewrite Results (changes applied)
- Compilation Results (success/errors)
- Next Steps (manual review items)

#### 2.5 Implement CLI Entry Point
**Function signature:**
```python
def main():
    """CLI entry point with argument parsing."""
```

**Requirements:**
- Use argparse for command-line arguments
- Arguments: --project-path, --dry-run, --verbose
- Set up logging based on verbosity
- Call run_migration_pipeline()
- Print report to stdout
- Exit with appropriate exit code

### Validation Steps

**1. Test project analysis:**
```bash
python -c "
from src.mvp_migrator import analyze_project
from src.config import TEST_PROJECT_PATH
result = analyze_project(TEST_PROJECT_PATH)
print(result)
"
# Should show file count, Spring Boot version, complexity
```

**2. Test compilation validation:**
```bash
python -c "
from src.validators import validate_compilation
from src.config import TEST_PROJECT_PATH
success, output = validate_compilation(TEST_PROJECT_PATH)
print(f'Compilation success: {success}')
"
# Should compile successfully on unmodified project
```

**3. Test full pipeline (dry-run equivalent):**
```bash
python src/mvp_migrator.py --project-path ./test-projects/spring-petclinic
# Should run end-to-end without crashing
# Should show all pipeline stages in logs
# Should generate markdown report
```

### Phase 2 Complete When:
- [x] validators.py compiles and validates successfully
- [x] analyze_project() returns accurate file counts and versions
- [x] run_migration_pipeline() executes all stages
- [x] Report generation produces readable markdown
- [x] CLI accepts arguments and runs pipeline
- [x] No crashes or unhandled exceptions

---

## Phase 3: Claude API Integration for Security Configs
**Goal:** Claude successfully migrates at least one Spring Security configuration  
**Estimated time:** 2 hours

### Tasks

#### 3.1 Set up tree-sitter for Java parsing
**Requirements:**
- Initialize tree-sitter Java parser
- Create query to find WebSecurityConfigurerAdapter classes
- Test query against sample Java code

**Implementation in claude_fixer.py:**
```python
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_java

# Initialize parser
JAVA_LANGUAGE = Language(tree_sitter_java.language())
parser = Parser(JAVA_LANGUAGE)

# Query for Security configs (tree-sitter 0.25 API: Query constructor + QueryCursor)
SECURITY_CONFIG_QUERY = Query(JAVA_LANGUAGE, """
(class_declaration
  (superclass
    (type_identifier) @superclass
    (#eq? @superclass "WebSecurityConfigurerAdapter")
  )
) @class
""")

# Usage:
# cursor = QueryCursor(SECURITY_CONFIG_QUERY)
# captures = cursor.captures(tree.root_node)  # returns dict {name: [nodes]}
```

#### 3.2 Implement Security Config Discovery
**Function signature:**
```python
def find_security_configs(project_path: Path) -> list[Path]:
    """
    Find all Java files extending WebSecurityConfigurerAdapter.
    
    Returns:
        List of file paths containing Security configs
    """
```

**Implementation steps:**
1. Recursively find all .java files
2. Parse each file with tree-sitter
3. Run SECURITY_CONFIG_QUERY against AST
4. Return paths of files with matches
5. Log count of configs found

#### 3.3 Implement Claude Migration Logic
**Function signature:**
```python
def migrate_security_config(file_path: Path) -> tuple[bool, str, int]:
    """
    Use Claude to migrate Spring Security config.

    Returns:
        (success: bool, migrated_code_or_error: str, tokens_used: int)
    """
```

**Implementation requirements:**
- Read original file content
- Build prompt from SPECIFICATION.md template
- Call Claude API with appropriate parameters
- Extract code from response
- Validate response contains valid Java
- Return migrated code

**Claude API call structure:**
```python
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

response = client.messages.create(
    model=CLAUDE_MODEL,
    max_tokens=4000,
    temperature=0.0,  # Deterministic for code generation
    messages=[{
        "role": "user",
        "content": prompt
    }]
)

code = response.content[0].text
tokens_used = response.usage.input_tokens + response.usage.output_tokens
```

#### 3.4 Implement Safe File Writing
**Function signature:**
```python
def write_migrated_file(file_path: Path, new_content: str) -> bool:
    """
    Write migrated code to file with backup.
    
    Creates .bak file before writing.
    Returns success status.
    """
```

#### 3.5 Integrate into Main Pipeline
**Modify run_migration_pipeline() to:**
1. After OpenRewrite step, call find_security_configs()
2. For each config found, call migrate_security_config()
3. Write migrated code with write_migrated_file()
4. Log token usage and success/failure
5. Continue with validation step

### Validation Steps

**1. Test Security config detection:**
```bash
python -c "
from src.claude_fixer import find_security_configs
from src.config import TEST_PROJECT_PATH
configs = find_security_configs(TEST_PROJECT_PATH)
print(f'Found {len(configs)} Security configs: {configs}')
"
# Should find WebSecurityConfigurerAdapter classes if they exist
```

**2. Test Claude API call with sample:**
Create a test file with Security config, then:
```bash
python -c "
from pathlib import Path
from src.claude_fixer import migrate_security_config
success, result = migrate_security_config(Path('test_security.java'))
print(f'Success: {success}')
print(result[:500])
"
# Should return migrated code with SecurityFilterChain pattern
```

**3. Validate migrated code parses:**
```bash
python -c "
from tree_sitter import Parser
import tree_sitter_java
# Parse migrated code
# Should parse without syntax errors
"
```

**4. Test integration in pipeline:**
```bash
python src/mvp_migrator.py --project-path ./test-projects/spring-petclinic
# Should find Security configs
# Should call Claude to migrate them
# Should write modified files
# Should show token usage in logs
```

### Phase 3 Complete When:
- [x] tree-sitter successfully parses Java files
- [x] Security config detection works (petclinic has 0 configs at commit 9ecdc111; validated with synthetic WebSecurityConfigurerAdapter file)
- [x] Claude API returns valid migrated code (validated with synthetic file, 723 tokens/call)
- [x] Migrated code parses as valid Java syntax
- [x] Files are written safely with backups
- [x] Token usage is logged for each Claude call
- [x] Integration in pipeline works end-to-end

---

## Phase 4: End-to-End Validation & Polish
**Goal:** Complete migration of spring-petclinic compiles successfully  
**Estimated time:** 90 minutes

### Tasks

#### 4.1 Create Fresh Test
**Setup:**
1. Reset existing spring-petclinic to clean state: `git checkout -- . && git clean -fd`
2. Verify it compiles on original version: `mvn clean compile`
3. Record baseline metrics (35 Java files, Spring Boot 2.7.3)

#### 4.2 Run Full Migration
**Execute:**
```bash
cd ~/projects/migration-mvp
python -m src.mvp_migrator --project-path ./test-projects/spring-petclinic
```

**Actual output:**
- Analysis: 35 Java files, Spring Boot 2.7.3, low complexity
- OpenRewrite applies 17 file changes (javax→jakarta, Boot 2.7.3→3.0.13, Java 1.8→17)
- Claude finds 0 security configs (petclinic has no Spring Security at this commit)
- Compilation succeeds (`mvn clean compile` exit 0)
- App runs (`mvn spring-boot:run` serves HTTP 200 on port 8080)
- Report generated

#### 4.3 Handle Compilation Errors
**If compilation fails:**
1. Parse error messages from Maven output
2. Identify which files failed
3. Determine if errors are:
   - OpenRewrite issues (report to user)
   - Claude migration issues (retry with refined prompt)
   - Unrelated to migration (report to user)
4. Document all errors in final report

**If Security config migration fails:**
1. Review Claude's output
2. Refine prompt template if needed
3. Add error handling for common issues:
   - Missing imports in migrated code
   - Incomplete lambda conversions
   - Missing return statement

#### 4.4 Measure Success Metrics
**Calculate and log:**
- Total files analyzed
- Files changed by OpenRewrite
- Files changed by Claude
- Automation percentage: (automated changes / total needed changes) × 100
- Compilation success: yes/no
- Token usage: total tokens across all Claude calls
- Runtime duration: total seconds

#### 4.5 Generate Final Report
**Enhance report with:**
- Executive summary (success/failure, key metrics)
- Detailed change breakdown (OpenRewrite vs Claude)
- Compilation results (errors if any)
- Manual review checklist:
  - Files that need human review
  - Known limitations
  - Next steps for production deployment
- Resource usage (tokens, runtime)

#### 4.6 Documentation Polish
**Update README.md with:**
- Actual usage example from successful run
- Known limitations discovered during testing
- Performance characteristics (runtime, token usage)
- Next steps for production version

**Create RESULTS.md:**
- Full migration report from test run
- Screenshots or terminal output snippets
- Analysis of what worked vs. what needs improvement

### Validation Steps

**1. Compilation check:**
```bash
cd test-projects/spring-petclinic
mvn clean compile
echo "Exit code: $?"
# Exit code must be 0 for success
```

**2. Verify app runs:**
```bash
cd test-projects/spring-petclinic
mvn spring-boot:run
# Open http://localhost:8080 in browser, Ctrl+C to stop
```

**3. Check report completeness:**
```bash
# Review generated report
# Must include all sections:
# - Summary, Analysis, Results, Errors (if any), Next Steps
```

**4. Verify metrics:**
```bash
# Confirm report shows:
# - Automation rate >50%
# - File counts accurate
# - Token usage logged
# - Runtime <5 minutes
```

### Phase 4 Complete When:
- [x] Fresh petclinic migrated successfully (17 files changed by OpenRewrite)
- [x] Code compiles without errors: `mvn clean compile` exits 0
- [x] App runs: `mvn spring-boot:run` serves HTTP 200
- [x] All metrics calculated and logged (49% automation, 57s runtime)
- [x] Comprehensive report generated (6 sections)
- [x] README updated with run instructions
- [x] No critical bugs or crashes

---

## Success Criteria Summary

**The MVP is complete when ALL of these are true:**

1. ✅ OpenRewrite runs successfully via subprocess (17 files changed)
2. ✅ Claude Security migration works (Phase 5: 5/5 configs migrated on synthetic + real projects, 100% success rate)
3. ✅ Migrated spring-petclinic compiles: `mvn clean compile` exits 0
4. ⚠️ Automation rate 49% (17/35 files — just under 50% target; all mechanically-needed changes were automated)
5. ✅ Total runtime ~57s (well under 5 min limit)
6. ✅ Token usage: 0 for petclinic run (no security configs); ~723 tokens per Claude call when used
7. ✅ Comprehensive report generated with all sections
8. ✅ No unhandled exceptions or crashes
9. ✅ Documentation is complete and accurate
10. ✅ Code is clean, 497 SLOC (under 500 limit)

---

## Debugging Tips for Claude Code

**If OpenRewrite fails:**
- Check Maven is installed: `mvn -version`
- Verify project has pom.xml at root
- Try running Maven command manually
- Check for network issues (OpenRewrite downloads dependencies)

**If Claude API fails:**
- Verify API key is set: `echo $ANTHROPIC_API_KEY`
- Check for rate limiting (wait 60s and retry)
- Reduce prompt size if hitting token limits
- Validate response structure before using

**If compilation fails:**
- Run `mvn clean compile` manually to see full errors
- Check if errors are in migrated files or unrelated
- Review specific error messages for clues
- Consider if OpenRewrite introduced issues

**If tree-sitter fails:**
- Verify tree-sitter-java is installed
- Check Java file encoding (should be UTF-8)
- Test with simple Java file first
- Review query syntax

---

## Phase 5: Validate Claude Integration with Real Security Configs
**Goal:** Prove Claude can migrate WebSecurityConfigurerAdapter → SecurityFilterChain on real projects
**Completed:** 2026-02-07

### Deliverables
- `test-cases/security_configs/` — 3 synthetic test cases (basic_form_auth, method_security, csrf_and_cors)
- `src/pattern_validators/security_validator.py` — SecurityMigrationValidator (10 validation checks)
- `test_security_migrations.py` — Test runner with JSON metrics output
- Enhanced Claude prompt in `claude_fixer.py` (13 rules, preserve list, complete-class instruction)
- `phase5_metrics.json` — Full metrics from all tests

### Results
- **Synthetic tests:** 3/3 passed, avg 863 tokens/config
- **Real project #1:** spring-boot-realworld-example-app (gothinkster) — Spring Boot 2.6.3, Gradle, JWT security config with CORS/CSRF/session management/custom filter → **PASS** (2,205 tokens)
- **Real project #2:** spring-boot-jwt (murraco) — Spring Boot 2.x, Maven, JWT security with @EnableGlobalMethodSecurity, dual configure() methods, WebSecurityCustomizer, AuthenticationManager → **PASS** (1,957 tokens)
- **Overall: 5/5 configs, 100% success rate, avg 1,350 tokens/config**

### Patterns Successfully Handled
- WebSecurityConfigurerAdapter removal → @Bean SecurityFilterChain
- authorizeRequests → authorizeHttpRequests + lambda DSL
- antMatchers → requestMatchers (including HttpMethod variants)
- .and() chaining → lambda DSL for csrf, cors, session, exceptions
- @EnableGlobalMethodSecurity → @EnableMethodSecurity
- configure(WebSecurity) → @Bean WebSecurityCustomizer
- authenticationManagerBean() → modern AuthenticationConfiguration pattern
- addFilterBefore preserved, http.apply() preserved
- Additional @Bean methods preserved (PasswordEncoder, CorsConfigurationSource, etc.)
- Comments and Lombok annotations preserved

### Success Criteria (from PHASE_5_SPEC.md)
- [x] At least 3 different Security config patterns migrate successfully (5 configs passed)
- [x] All migrated configs parse as valid Java
- [x] Validation detects when rules are lost or incorrect (10 checks in SecurityMigrationValidator)
- [x] Token usage reasonable <5K per config (avg 1,350 tokens)
- [x] Test runner passes 100% on synthetic test cases (3/3)
- [x] Tested against 2+ real open-source projects (realworld-jwt + spring-boot-jwt)
- [x] Success rate >80% on real projects (100%)

---

## Phase 6: Additional Claude Migration Patterns
**Goal:** Add config properties and Hibernate 6 migration patterns, plus an orchestrator to coordinate all pattern types
**Completed:** 2026-02-07

### Architecture
- **Prompt templates** in `prompts/` (security_filterchain.txt, config_properties.txt, hibernate_six.txt)
- **Migration patterns** in `src/migration_patterns/` (config_properties.py, hibernate_six.py)
- **PatternOrchestrator** in `src/orchestrator.py` — coordinates all 3 pattern types with graceful degradation
- Stage 3 of pipeline upgraded from "Security-only" to "Claude Pattern Migrations" (security + config + hibernate)

### Deliverables
- `prompts/` — 3 prompt templates (extracted from inline, versionable)
- `src/migration_patterns/config_properties.py` — Detects deprecated Boot 2.x properties, calls Claude to migrate
- `src/migration_patterns/hibernate_six.py` — Detects @Type/@TypeDef annotations and deprecated dialects via tree-sitter
- `src/orchestrator.py` — PatternOrchestrator class with per-pattern error isolation
- `test-cases/config_properties/` — 2 test cases (properties + YAML)
- `test-cases/hibernate_patterns/` — 2 test cases (json_type entity + dialect config)
- `test-cases/security_configs/websecurity_ignoring.java` — New test: dual configure() with WebSecurity ignoring
- `test_pattern_migrations.py` — Multi-pattern test runner
- `phase6_metrics.json` — Full metrics from all tests

### Results
- **Config properties:** 2/2 passed (application.properties + YAML), avg 1,256 tokens
- **Hibernate 6:** 2/2 passed (json_type entity + dialect config), avg 1,634 tokens
- **Security:** 4/4 passed (3 existing + 1 new websecurity_ignoring), avg 974 tokens
- **Overall: 8/8 test cases, 100% success rate, avg 1,210 tokens/file**
- **Regression:** Phase 5 security tests still pass 4/4

### Patterns Successfully Handled
- **Config:** spring.redis → spring.data.redis, elasticsearch.rest → elasticsearch, deprecated property removal, dialect renames in config values, custom property preservation
- **Hibernate:** @TypeDef/@TypeDefs removal, @Type(type="json") → @JdbcTypeCode(SqlTypes.JSON), @Type(type="uuid-char") → @JdbcTypeCode(SqlTypes.VARCHAR), @Type(type="yes_no") → @Convert(YesNoConverter), MySQL5Dialect → MySQLDialect, javax.persistence → jakarta.persistence
- **Security:** All Phase 5 patterns + WebSecurity.ignoring() → WebSecurityCustomizer

### Key Learning
- Python `.format()` fails on Java code containing `{}` (generics like `Map<String, Object>`) — use `.replace()` for prompt template substitution instead

---

## Post-MVP Next Steps

After successful MVP, consider:

1. **Expand Claude patterns:**
   - ~~Hibernate 5→6 migration~~ (done in Phase 6)
   - ~~Configuration file migration~~ (done in Phase 6)
   - Custom annotation migrations

2. **Add LangGraph:**
   - State machine orchestration
   - Retry loops with learning
   - Multi-agent collaboration

3. **Improve validation:**
   - Test execution
   - Static analysis integration
   - Characterization test generation

4. **Production hardening:**
   - Git integration
   - CI/CD pipeline
   - Error recovery
   - Parallel processing

5. **Test on real monoliths:**
   - Larger codebases (>100K LOC)
   - More complex Security configs
   - Custom Spring Boot starters
   - Legacy code patterns

This plan is complete and ready for Claude Code execution.

