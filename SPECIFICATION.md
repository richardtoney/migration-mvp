# Spring Boot Migration MVP - Technical Specification

## Mission Statement

Build a Python CLI tool that combines OpenRewrite automated refactoring with Claude API intelligent code generation to migrate Spring Boot 2.7 applications to Spring Boot 3.0, achieving >50% automation rate with <5% error rate on the spring-petclinic reference project.

**Target outcome:** Demonstrate that AI-assisted migration can handle mechanical transformations (via OpenRewrite) and complex pattern refactoring (via Claude) more efficiently than manual migration, in 8 hours of development time.

## Architectural Decisions (LOCKED)

These decisions are final and cannot be changed during MVP development:

1. **Language:** Python 3.11+
   - Rationale: Developer expertise, rich ecosystem, subprocess integration

2. **Architecture:** Single-script sequential pipeline (no frameworks)
   - Rationale: Simplicity for MVP, LangGraph deferred to production version
   - Structure: analyze → openrewrite → identify-gaps → claude-fix → validate

3. **OpenRewrite Integration:** CLI via subprocess
   - Rationale: No build file modification required, works on any Maven project
   - Method: Direct Maven plugin invocation with `-D` parameters

4. **Claude Integration:** Anthropic Python SDK
   - Rationale: Official SDK, handles rate limits, typed responses
   - Model: claude-sonnet-4-5 (fast, cost-effective for code tasks)

5. **Test Project:** spring-projects/spring-petclinic
   - Rationale: Official Spring sample, realistic complexity, good test coverage
   - Version: Spring Boot 2.7.3 (commit 9ecdc1111e3da388a750ace41a125287d9620534)

6. **Success Metric:** Code compiles (`mvn compile` exits 0)
   - Rationale: Compilation proves 70%+ of migration succeeded
   - Test execution deferred to production version

## Hard Constraints

**CANNOT do:**
- Modify test project's pom.xml to add OpenRewrite plugin
- Use embedded Java tools (JPype, Py4J) - subprocess only
- Execute tests as part of validation (compilation only)
- Implement retry loops or error recovery (manual intervention expected)
- Handle multiple complex patterns (limit to ONE: Spring Security configs)

**MUST do:**
- Work on unmodified spring-petclinic checkout
- Use only Python standard library + pip packages
- Complete in <500 lines of total Python code
- Process files in-place (no separate output directory)
- Log all actions with timestamps and status

## File Structure (REQUIRED)

```
migration-mvp/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration, constants, env vars
│   ├── openrewrite_runner.py  # OpenRewrite subprocess wrapper
│   ├── claude_fixer.py         # Claude API integration
│   ├── validators.py           # Compilation validation
│   └── mvp_migrator.py         # Main orchestration script
├── test-projects/
│   └── spring-petclinic/       # Cloned from GitHub
├── docs/
│   └── security-migration-example.md
├── SPECIFICATION.md            # This file
├── DEVELOPMENT_PLAN.md         # Phase-by-phase plan
├── requirements.txt
├── .env                        # API keys (not in git)
├── .gitignore
└── README.md
```

## Module Responsibilities

### config.py
```python
"""
Configuration and constants for the migration tool.
Loads from .env file and provides typed access to settings.
"""
- ANTHROPIC_API_KEY: str
- CLAUDE_MODEL: str
- TEST_PROJECT_PATH: Path
- OPENREWRITE_VERSION: str
- LOG_LEVEL: str
```

### openrewrite_runner.py
```python
"""
OpenRewrite subprocess integration.
Runs OpenRewrite Maven plugin without modifying build files.
"""
def run_openrewrite(project_path: Path, recipe: str, dry_run: bool = False) -> tuple[bool, str]:
    """
    Execute OpenRewrite recipe via Maven plugin.
    
    Args:
        project_path: Path to Maven project
        recipe: Fully qualified recipe name
        dry_run: If True, preview changes without applying
    
    Returns:
        (success: bool, output: str)
    """
```

### claude_fixer.py
```python
"""
Claude API integration for complex code transformations.
Currently handles Spring Security config migration only.
"""
def find_security_configs(project_path: Path) -> list[Path]:
    """Use tree-sitter to find WebSecurityConfigurerAdapter classes."""

def migrate_security_config(file_path: Path) -> tuple[bool, str]:
    """
    Use Claude to migrate Spring Security config from 2.x to 3.x pattern.
    
    Sends original file to Claude with migration instructions,
    receives updated code, validates syntax, writes back to file.
    """
```

### validators.py
```python
"""
Validation tools for migration pipeline.
"""
def validate_compilation(project_path: Path) -> tuple[bool, str]:
    """Run mvn clean compile and parse output."""

def parse_compilation_errors(maven_output: str) -> list[dict]:
    """Extract file paths and error messages from Maven output."""
```

### mvp_migrator.py
```python
"""
Main orchestration script.
Implements the sequential pipeline: analyze → migrate → validate → report.
"""
def analyze_project(project_path: Path) -> dict:
    """Count files, parse pom.xml, estimate scope."""

def run_migration_pipeline(project_path: Path) -> dict:
    """Execute full migration and return results."""

def generate_report(results: dict) -> str:
    """Format migration results as markdown report."""

def main():
    """CLI entry point."""
```

## Success Criteria (TESTABLE)

Each criterion must be verified before considering MVP complete:

1. ✅ **OpenRewrite runs successfully**
   - Command completes without error
   - Applies >50 transformations to petclinic
   - Output shows "Changes have been made"

2. ✅ **At least 1 Security config migrated via Claude**
   - Finds WebSecurityConfigurerAdapter classes
   - Generates valid SecurityFilterChain replacement
   - Modified code parses as valid Java (tree-sitter validates)

3. ✅ **Modified code compiles**
   - `mvn clean compile` in test-project exits with code 0
   - No compilation errors in Maven output
   - All classes and resources packaged successfully

4. ✅ **Migration report generated**
   - Shows: files analyzed, files changed, automation %
   - Lists: manual review items, known issues
   - Includes: runtime duration, success/failure status

5. ✅ **Total runtime < 5 minutes**
   - On standard laptop hardware
   - For spring-petclinic (5K LOC)
   - Including OpenRewrite, Claude calls, compilation

## Explicitly Out of Scope

Do NOT implement these in the MVP:

- ❌ LangGraph state machine orchestration
- ❌ Git integration (commits, branches, tags)
- ❌ Test execution or test generation
- ❌ Retry loops or error recovery logic
- ❌ Multiple Claude fix patterns (only Security configs)
- ❌ ICEfaces migration logic
- ❌ Database schema migration
- ❌ Configuration file migration (properties/yaml)
- ❌ Parallel file processing
- ❌ Web UI or API server
- ❌ Detailed progress bars or UX polish

## Reference Materials

### OpenRewrite Commands

**Dry-run mode (preview changes — uses `dryRun` goal):**
```bash
mvn -U org.openrewrite.maven:rewrite-maven-plugin:6.28.0:dryRun \
  -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE \
  -Drewrite.activeRecipes=org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0
```

**Apply changes (uses `run` goal):**
```bash
mvn -U org.openrewrite.maven:rewrite-maven-plugin:6.28.0:run \
  -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE \
  -Drewrite.activeRecipes=org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0
```

**Key recipes for Spring Boot 2.7 → 3.0:**
- `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0` (composite recipe)
- Includes: javax→jakarta namespace changes
- Includes: Spring Boot dependency version updates
- Includes: Deprecated API replacements

### Spring Security Migration Pattern

**BEFORE (Spring Boot 2.x - WebSecurityConfigurerAdapter):**
```java
package org.springframework.samples.petclinic.system;

import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;

@Configuration
@EnableWebSecurity
public class SecurityConfiguration extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/resources/**", "/webjars/**", "/h2-console/**").permitAll()
                .anyRequest().authenticated()
            .and()
            .formLogin()
                .loginPage("/login")
                .permitAll()
            .and()
            .logout()
                .logoutSuccessUrl("/")
                .permitAll()
            .and()
            .csrf()
                .ignoringAntMatchers("/h2-console/**");
    }
}
```

**AFTER (Spring Boot 3.x - SecurityFilterChain):**
```java
package org.springframework.samples.petclinic.system;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfiguration {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers("/resources/**", "/webjars/**", "/h2-console/**").permitAll()
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .permitAll()
            )
            .logout(logout -> logout
                .logoutSuccessUrl("/")
                .permitAll()
            )
            .csrf(csrf -> csrf
                .ignoringRequestMatchers("/h2-console/**")
            );
        return http.build();
    }
}
```

**Key transformation rules:**
1. Remove `extends WebSecurityConfigurerAdapter`
2. Change `protected void configure(HttpSecurity http)` to `@Bean public SecurityFilterChain filterChain(HttpSecurity http)`
3. Replace `.authorizeRequests()` with `.authorizeHttpRequests(authorize -> ...)`
4. Replace `.antMatchers()` with `.requestMatchers()`
5. Replace `.and()` chaining with lambda DSL
6. Add `return http.build();` at end
7. Add import: `org.springframework.security.web.SecurityFilterChain`
8. May need: `org.springframework.security.config.Customizer` for default configs

### tree-sitter Java Query for Security Configs

```python
# Query to find WebSecurityConfigurerAdapter classes
SECURITY_CONFIG_QUERY = """
(class_declaration
  (superclass
    (type_identifier) @superclass
    (#eq? @superclass "WebSecurityConfigurerAdapter")
  )
) @class
"""

# Usage with tree-sitter:
# tree = parser.parse(source_code)
# captures = query.captures(tree.root_node)
```

### Maven Compilation Validation

```bash
# Clean compile (ensures fresh build)
mvn clean compile

# Exit codes:
# 0 = Success
# Non-zero = Compilation failed

# Parsing output for errors:
# Lines starting with "[ERROR]" contain compilation errors
# Format: [ERROR] /path/to/File.java:[line,col] error message
```

## Error Handling Requirements

**Subprocess calls:**
- Capture both stdout and stderr
- Check return code explicitly
- Log full command and output on failure
- Do NOT use `shell=True` (security risk)

**File operations:**
- Validate paths exist before reading
- Use `Path.resolve()` to handle relative paths
- Handle encoding errors (use utf-8 with error handling)
- Create backup before modifying files

**Claude API calls:**
- Catch `anthropic.APIError` and log full error
- Retry once on rate limit (status 429)
- Validate response contains code before writing files
- Log token usage for each call

**Do NOT:**
- Use bare `except:` clauses
- Silently swallow errors
- Continue processing after critical failures
- Assume file encodings (always specify)

## Logging Requirements

Use Python's `logging` module with this format:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log levels:
# DEBUG: Detailed diagnostic info
# INFO: Major pipeline stages
# WARNING: Recoverable issues
# ERROR: Failures that stop processing
```

**What to log:**
- Pipeline stage transitions
- File counts and paths being processed
- OpenRewrite command and output
- Claude API calls (prompt summary, token usage)
- Compilation results (success/error count)
- Final report generation

## Claude API Prompt Template

When calling Claude to migrate Security configs:

```python
SECURITY_MIGRATION_PROMPT = """You are migrating a Spring Security configuration from Spring Boot 2.x to Spring Boot 3.x.

The key changes are:
1. WebSecurityConfigurerAdapter is removed - use @Bean SecurityFilterChain instead
2. authorizeRequests() → authorizeHttpRequests()
3. antMatchers() → requestMatchers()
4. Method chaining with .and() → Lambda DSL
5. Must return http.build() from the method

Here is the original security configuration:

```java
{original_code}
```

Migrate this to Spring Boot 3.x pattern. Return ONLY the migrated Java code, no explanations.
Preserve all the original security rules and behavior.
"""
```

## Development Environment

**Required:**
- Arch Linux or compatible system
- Python 3.11+
- JDK 17
- Maven 3.6+
- Git

**Python packages (requirements.txt):**
```
anthropic>=0.39.0
tree-sitter>=0.23.0
tree-sitter-java>=0.23.4
lxml>=5.1.0
requests>=2.31.0
python-dotenv>=1.0.0
```

**Environment variables (.env):**
```bash
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929
TEST_PROJECT_PATH=./test-projects/spring-petclinic
OPENREWRITE_VERSION=6.28.0
LOG_LEVEL=INFO
```

## Validation Checklist

Before marking a phase complete, verify:

**Phase 1 (OpenRewrite Integration):**
- [ ] OpenRewrite command executes without error
- [ ] Dry-run shows planned changes in output
- [ ] Can parse Maven output to extract change count
- [ ] Logs show OpenRewrite version and recipe used

**Phase 2 (Basic Orchestration):**
- [ ] Main script runs end-to-end without crash
- [ ] Project analysis counts files correctly
- [ ] OpenRewrite changes are applied (not dry-run)
- [ ] Validation attempts compilation
- [ ] Structured logging shows all pipeline stages

**Phase 3 (Claude Integration):**
- [ ] tree-sitter finds Security config classes
- [ ] Claude API call succeeds with valid response
- [ ] Generated code parses as valid Java
- [ ] Modified file is written back to disk
- [ ] Token usage is logged

**Phase 4 (End-to-End):**
- [ ] Full pipeline on clean petclinic checkout succeeds
- [ ] `mvn clean compile` exits 0 in test-project
- [ ] Migration report contains all required sections
- [ ] Manual review list is accurate
- [ ] Total runtime < 5 minutes

## Known Limitations

Document these in final report:

1. **Single pattern only:** MVP handles Security configs; other complex patterns require manual review
2. **No test execution:** Compilation proves syntax, not runtime behavior
3. **No rollback:** Failed migrations require manual git reset
4. **No parallel processing:** Files processed sequentially
5. **Limited error recovery:** Most failures stop pipeline

## Success Metrics

**Quantitative:**
- Files changed: >10
- Automation rate: >50% (calculated as: OpenRewrite changes / total needed changes)
- Compilation success: 100% (must compile cleanly)
- Runtime: <5 minutes
- Token usage: <100K tokens total

**Qualitative:**
- Code quality: Modified code is readable and maintainable
- Safety: No behavioral changes beyond Spring Boot 3.x requirements
- Completeness: All mechanical changes handled, gaps clearly documented

## Next Steps After MVP

If MVP succeeds, production version should add:

1. LangGraph orchestration with retry loops
2. Multiple Claude fix patterns (not just Security)
3. Characterization test generation
4. Git integration with atomic commits
5. Configuration file migration (properties/yaml)
6. Comprehensive error recovery
7. Parallel file processing
8. CI/CD integration

This specification is complete and locked for MVP development.

