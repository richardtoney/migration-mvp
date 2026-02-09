# Phase 6: Add More Claude Migration Patterns

## Overview
**Goal:** Increase automation rate from 49% to >70% by adding 3-4 high-value Claude migration patterns beyond Security configs.

**Time estimate:** 8-12 hours  
**Priority:** HIGH - This is what makes the tool genuinely valuable

---

## Why This Phase Matters

Your MVP achieved **49% automation** (17/35 changes on petclinic). OpenRewrite handled mechanical changes but missed patterns requiring semantic understanding. Adding just 3-4 more Claude patterns will:

- Jump automation to >70% (meeting your success criteria)
- Handle the "long tail" of complex migrations
- Prove the agent can scale to real monoliths
- Reduce manual review burden significantly

---

## Architecture Changes

### New Directory Structure

```
migration-mvp/
├── src/
│   ├── migration_patterns/       # NEW - Pattern-specific modules
│   │   ├── __init__.py
│   │   ├── base_pattern.py       # Abstract base class
│   │   ├── security_advanced.py  # Enhanced Security patterns
│   │   ├── config_properties.py  # application.properties migration
│   │   ├── hibernate_six.py      # Hibernate 5→6 patterns
│   │   └── test_migration.py     # JUnit 4→5 (if needed)
│   ├── orchestrator.py           # NEW - Pattern orchestration
│   └── ...existing files...
├── prompts/                       # NEW - Reusable prompt templates
│   ├── security_filterchain.txt
│   ├── config_properties.txt
│   └── hibernate_custom_types.txt
└── test-cases/
    ├── security_configs/         # From Phase 5
    ├── config_properties/        # NEW
    └── hibernate_patterns/       # NEW
```

---

## Pattern 1: Spring Security Advanced Patterns (3-4 hours)

### Scope
Beyond basic WebSecurityConfigurerAdapter → SecurityFilterChain, handle:

1. **WebSecurity configuration (ignoring paths)**
2. **Custom AuthenticationProvider beans**
3. **OAuth2 client configuration**
4. **Remember-me authentication**
5. **Session management**

### Implementation: src/migration_patterns/security_advanced.py

```python
"""
Advanced Spring Security migration patterns.
Handles edge cases beyond basic WebSecurityConfigurerAdapter.
"""
from pathlib import Path
from typing import Tuple, List
import re
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


class SecurityAdvancedMigrator:
    """Handles complex Security migration patterns."""
    
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> dict:
        """Load prompt templates from files."""
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        return {
            "websecurity": (prompts_dir / "security_websecurity.txt").read_text(),
            "oauth2_client": (prompts_dir / "security_oauth2.txt").read_text(),
            "remember_me": (prompts_dir / "security_remember_me.txt").read_text(),
        }
    
    def detect_pattern(self, code: str) -> str:
        """Identify which Security pattern is present."""
        if "WebSecurity" in code and "ignoring()" in code:
            return "websecurity"
        elif "oauth2Login" in code or "OAuth2AuthorizedClientService" in code:
            return "oauth2_client"
        elif "rememberMe()" in code:
            return "remember_me"
        return "standard"
    
    def migrate(self, file_path: Path) -> Tuple[bool, str, int]:
        """
        Migrate advanced Security patterns.
        
        Returns:
            (success, migrated_code or error, tokens_used)
        """
        code = file_path.read_text()
        pattern = self.detect_pattern(code)
        
        if pattern == "standard":
            # Delegate to basic migrator from Phase 5
            return False, "No advanced patterns detected", 0
        
        prompt = self.prompts[pattern].format(
            original_code=code,
            pattern_type=pattern
        )
        
        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            migrated_code = response.content[0].text.strip()
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Validate migration
            if self._validate_migration(code, migrated_code, pattern):
                return True, migrated_code, tokens_used
            else:
                return False, "Validation failed", tokens_used
                
        except Exception as e:
            return False, f"Claude API error: {str(e)}", 0
    
    def _validate_migration(self, original: str, migrated: str, pattern: str) -> bool:
        """Pattern-specific validation."""
        if pattern == "websecurity":
            # Should have WebSecurityCustomizer bean
            return "@Bean" in migrated and "WebSecurityCustomizer" in migrated
        elif pattern == "oauth2_client":
            # Should preserve OAuth2 configuration
            return "oauth2Login" in migrated or "authorizedClientService" in migrated
        return True
```

### Test Cases: test-cases/security_configs/

**websecurity_ignoring.java:**
```java
@Configuration
@EnableWebSecurity
public class WebSecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Override
    public void configure(WebSecurity web) throws Exception {
        web.ignoring()
            .antMatchers("/resources/**", "/static/**", "/css/**", "/js/**", "/images/**");
    }
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests()
            .anyRequest().authenticated()
            .and()
            .formLogin();
    }
}
```

**Expected migration:**
```java
@Configuration
@EnableWebSecurity
public class WebSecurityConfig {
    
    @Bean
    public WebSecurityCustomizer webSecurityCustomizer() {
        return (web) -> web.ignoring()
            .requestMatchers("/resources/**", "/static/**", "/css/**", "/js/**", "/images/**");
    }
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth
                .anyRequest().authenticated())
            .formLogin(Customizer.withDefaults());
        return http.build();
    }
}
```

### Prompt Template: prompts/security_websecurity.txt

```
You are migrating Spring Security from Spring Boot 2.x to 3.x.

PATTERN DETECTED: {pattern_type}

CRITICAL TRANSFORMATIONS FOR WEBSECURITY PATTERN:
1. Extract configure(WebSecurity web) into separate @Bean WebSecurityCustomizer
2. Change web.ignoring().antMatchers() to web.ignoring().requestMatchers()
3. Configure(HttpSecurity) becomes @Bean SecurityFilterChain as usual
4. Import org.springframework.security.config.annotation.web.configuration.WebSecurityCustomizer

STRUCTURE:
```java
@Bean
public WebSecurityCustomizer webSecurityCustomizer() {
    return (web) -> web.ignoring()
        .requestMatchers(...);  // Convert antMatchers to requestMatchers
}

@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    // Existing HttpSecurity config migrated to lambda DSL
    return http.build();
}
```

Here is the original code:

```java
{original_code}
```

Return ONLY the migrated Java code with no explanations.
```

---

## Pattern 2: Configuration Properties Migration (2-3 hours)

### Scope
Migrate application.properties and application.yml:

- Renamed properties (server.error.whitelabel → server.error.include-message)
- Restructured properties (spring.datasource.* → spring.datasource.hikari.*)
- Deprecated properties (spring.http.converters → spring.mvc.converters)
- JPA/Hibernate property changes

### Implementation: src/migration_patterns/config_properties.py

```python
"""
Migrates application.properties and application.yml files.
"""
from pathlib import Path
from typing import Tuple, Dict, List
import re
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


# Property rename mappings (OpenRewrite doesn't handle all of these)
PROPERTY_RENAMES = {
    # Spring Boot 2→3 property changes not caught by OpenRewrite
    "spring.http.log-request-details": "spring.mvc.log-request-details",
    "spring.mvc.throw-exception-if-no-handler-found": "spring.mvc.problemdetails.enabled",
    "spring.jpa.hibernate.use-new-id-generator-mappings": None,  # Removed, always true in 3.x
    "spring.data.web.pageable.default-page-size": "spring.data.web.pageable.default-page-size",
    "management.metrics.export.prometheus.enabled": "management.prometheus.metrics.export.enabled",
}


class ConfigPropertiesMigrator:
    """Migrates Spring Boot configuration files."""
    
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def find_config_files(self, project_path: Path) -> List[Path]:
        """Find all application.properties and application.yml files."""
        config_files = []
        
        # Search in src/main/resources
        resources_dir = project_path / "src" / "main" / "resources"
        if resources_dir.exists():
            config_files.extend(resources_dir.glob("application*.properties"))
            config_files.extend(resources_dir.glob("application*.yml"))
            config_files.extend(resources_dir.glob("application*.yaml"))
        
        return config_files
    
    def migrate(self, file_path: Path) -> Tuple[bool, str, int]:
        """
        Migrate configuration file properties.
        
        Returns:
            (success, migrated_content or error, tokens_used)
        """
        content = file_path.read_text()
        
        # Determine file type
        is_yaml = file_path.suffix in ['.yml', '.yaml']
        
        # Build prompt
        prompt = self._build_prompt(content, is_yaml)
        
        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            migrated_content = response.content[0].text.strip()
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return True, migrated_content, tokens_used
            
        except Exception as e:
            return False, f"Claude API error: {str(e)}", 0
    
    def _build_prompt(self, content: str, is_yaml: bool) -> str:
        """Build Claude prompt for config migration."""
        file_type = "YAML" if is_yaml else "Properties"
        
        return f"""You are migrating Spring Boot configuration from 2.7 to 3.x.

FILE TYPE: {file_type}

KNOWN PROPERTY CHANGES IN SPRING BOOT 3.x:
1. server.error.whitelabel.enabled → server.error.include-message
2. spring.jpa.hibernate.use-new-id-generator-mappings → REMOVED (always true)
3. spring.http.* → spring.mvc.* (most properties)
4. management.metrics.export.prometheus.* → management.prometheus.metrics.export.*
5. spring.data.rest.* → spring.data.web.*

INSTRUCTIONS:
- Update deprecated/renamed properties to their Spring Boot 3.x equivalents
- Remove properties that no longer exist
- Preserve comments and formatting
- Keep the same file structure
- Do NOT change property values, only property keys

Here is the original configuration:

```{file_type.lower()}
{content}
```

Return ONLY the migrated configuration with no explanations or markdown formatting.
"""
```

### Test Cases: test-cases/config_properties/

**application-before.properties:**
```properties
# Server configuration
server.error.whitelabel.enabled=true
server.port=8080

# Data source
spring.datasource.url=jdbc:mysql://localhost:3306/mydb
spring.datasource.username=root
spring.datasource.password=secret

# JPA/Hibernate
spring.jpa.hibernate.ddl-auto=update
spring.jpa.hibernate.use-new-id-generator-mappings=true
spring.jpa.show-sql=true

# HTTP logging
spring.http.log-request-details=true

# Metrics
management.metrics.export.prometheus.enabled=true
```

**application-after.properties (expected):**
```properties
# Server configuration
server.error.include-message=always
server.port=8080

# Data source
spring.datasource.url=jdbc:mysql://localhost:3306/mydb
spring.datasource.username=root
spring.datasource.password=secret

# JPA/Hibernate
spring.jpa.hibernate.ddl-auto=update
# spring.jpa.hibernate.use-new-id-generator-mappings removed in Spring Boot 3.x
spring.jpa.show-sql=true

# HTTP logging
spring.mvc.log-request-details=true

# Metrics
management.prometheus.metrics.export.enabled=true
```

---

## Pattern 3: Hibernate 5→6 Custom Types (2-3 hours)

### Scope
Hibernate 6.x (bundled with Spring Boot 3.x) has breaking changes:

1. **@Type annotation changes** - `@Type(type = "...")` → `@JdbcTypeCode`
2. **Custom UserType API changes**
3. **Dialect class renames** - `MySQL5Dialect` → `MySQLDialect`
4. **Type mappings** - JSON, UUID, array types

### Implementation: src/migration_patterns/hibernate_six.py

```python
"""
Migrates Hibernate 5 patterns to Hibernate 6.
"""
from pathlib import Path
from typing import Tuple
import re
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


class HibernateSixMigrator:
    """Handles Hibernate 5→6 migration patterns."""
    
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def detect_hibernate_patterns(self, code: str) -> List[str]:
        """Detect which Hibernate patterns need migration."""
        patterns = []
        
        if '@Type(type = ' in code or '@TypeDef' in code:
            patterns.append("custom_type")
        if 'MySQL5Dialect' in code or 'PostgreSQL9Dialect' in code:
            patterns.append("dialect")
        if 'implements UserType' in code:
            patterns.append("user_type_impl")
        
        return patterns
    
    def migrate(self, file_path: Path) -> Tuple[bool, str, int]:
        """
        Migrate Hibernate 5 code to Hibernate 6.
        
        Returns:
            (success, migrated_code or error, tokens_used)
        """
        code = file_path.read_text()
        patterns = self.detect_hibernate_patterns(code)
        
        if not patterns:
            return False, "No Hibernate 5 patterns detected", 0
        
        prompt = self._build_prompt(code, patterns)
        
        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            migrated_code = response.content[0].text.strip()
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return True, migrated_code, tokens_used
            
        except Exception as e:
            return False, f"Claude API error: {str(e)}", 0
    
    def _build_prompt(self, code: str, patterns: List[str]) -> str:
        """Build Claude prompt for Hibernate migration."""
        pattern_guidance = ""
        
        if "custom_type" in patterns:
            pattern_guidance += """
CUSTOM @Type MIGRATION:
- @Type(type = "json") → @JdbcTypeCode(SqlTypes.JSON)
- @Type(type = "uuid-char") → @JdbcType(UUIDJavaType.class)
- Import: org.hibernate.annotations.JdbcTypeCode
- Import: org.hibernate.type.SqlTypes
"""
        
        if "dialect" in patterns:
            pattern_guidance += """
DIALECT MIGRATION:
- MySQL5Dialect → MySQLDialect (or MySQL8Dialect)
- PostgreSQL9Dialect → PostgreSQLDialect
- Oracle10gDialect → OracleDialect
"""
        
        if "user_type_impl" in patterns:
            pattern_guidance += """
USERTYPE INTERFACE CHANGES:
- nullSafeGet signature changed: ResultSet + String[] → Object + SharedSessionContractImplementor
- nullSafeSet signature changed
- See Hibernate 6 UserType documentation for exact signatures
"""
        
        return f"""You are migrating Hibernate 5 code to Hibernate 6 (Spring Boot 3.x).

DETECTED PATTERNS: {', '.join(patterns)}

{pattern_guidance}

GENERAL RULES:
1. Preserve all business logic
2. Update imports (org.hibernate.type.* may have moved)
3. Maintain field names and types
4. Keep comments and formatting

Here is the original code:

```java
{code}
```

Return ONLY the migrated Java code with no explanations.
"""
```

### Test Case: test-cases/hibernate_patterns/json_type.java

**Before (Hibernate 5):**
```java
import org.hibernate.annotations.Type;
import javax.persistence.*;

@Entity
@Table(name = "documents")
public class Document {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Type(type = "json")
    @Column(columnDefinition = "json")
    private Map<String, Object> metadata;
    
    @Type(type = "uuid-char")
    @Column(length = 36)
    private UUID trackingId;
}
```

**After (Hibernate 6):**
```java
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import jakarta.persistence.*;
import java.util.UUID;

@Entity
@Table(name = "documents")
public class Document {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "json")
    private Map<String, Object> metadata;
    
    @Column(length = 36)
    private UUID trackingId;  // UUID type is native in Hibernate 6
}
```

---

## Pattern Orchestration

### Create src/orchestrator.py

This coordinates pattern detection and migration:

```python
"""
Orchestrates pattern detection and migration across multiple pattern types.
"""
from pathlib import Path
from typing import List, Dict, Tuple
import logging

from migration_patterns.security_advanced import SecurityAdvancedMigrator
from migration_patterns.config_properties import ConfigPropertiesMigrator
from migration_patterns.hibernate_six import HibernateSixMigrator

logger = logging.getLogger(__name__)


class PatternOrchestrator:
    """Coordinates all pattern-based migrations."""
    
    def __init__(self):
        self.migrators = {
            'security': SecurityAdvancedMigrator(),
            'config': ConfigPropertiesMigrator(),
            'hibernate': HibernateSixMigrator(),
        }
        self.results = {
            'files_processed': 0,
            'files_migrated': 0,
            'tokens_used': 0,
            'by_pattern': {}
        }
    
    def run(self, project_path: Path) -> Dict:
        """
        Run all pattern migrations on project.
        
        Returns:
            Migration statistics
        """
        logger.info("Starting pattern-based migration")
        
        # Migrate configuration files first
        self._migrate_configs(project_path)
        
        # Migrate Java files
        java_files = self._find_java_files(project_path)
        for java_file in java_files:
            self._migrate_java_file(java_file)
        
        # Generate report
        return self._generate_report()
    
    def _migrate_configs(self, project_path: Path):
        """Migrate application.properties and .yml files."""
        config_migrator = self.migrators['config']
        config_files = config_migrator.find_config_files(project_path)
        
        for config_file in config_files:
            logger.info(f"Migrating config: {config_file.name}")
            success, content, tokens = config_migrator.migrate(config_file)
            
            if success:
                config_file.write_text(content)
                self.results['files_migrated'] += 1
                logger.info(f"✅ Migrated {config_file.name}")
            
            self.results['files_processed'] += 1
            self.results['tokens_used'] += tokens
            self._track_pattern_result('config', success)
    
    def _migrate_java_file(self, file_path: Path):
        """Attempt to migrate a Java file with appropriate pattern."""
        code = file_path.read_text()
        migrated = False
        
        # Try Security patterns
        if 'WebSecurityConfigurerAdapter' in code or 'WebSecurityCustomizer' in code:
            success, content, tokens = self.migrators['security'].migrate(file_path)
            if success:
                file_path.write_text(content)
                migrated = True
                self.results['files_migrated'] += 1
                logger.info(f"✅ Migrated Security config: {file_path.name}")
            self.results['tokens_used'] += tokens
            self._track_pattern_result('security', success)
        
        # Try Hibernate patterns
        if not migrated and ('@Type' in code or 'UserType' in code):
            success, content, tokens = self.migrators['hibernate'].migrate(file_path)
            if success:
                file_path.write_text(content)
                migrated = True
                self.results['files_migrated'] += 1
                logger.info(f"✅ Migrated Hibernate code: {file_path.name}")
            self.results['tokens_used'] += tokens
            self._track_pattern_result('hibernate', success)
        
        if not migrated:
            logger.debug(f"No patterns detected in {file_path.name}")
        
        self.results['files_processed'] += 1
    
    def _track_pattern_result(self, pattern: str, success: bool):
        """Track success/failure by pattern type."""
        if pattern not in self.results['by_pattern']:
            self.results['by_pattern'][pattern] = {'success': 0, 'failed': 0}
        
        if success:
            self.results['by_pattern'][pattern]['success'] += 1
        else:
            self.results['by_pattern'][pattern]['failed'] += 1
    
    def _find_java_files(self, project_path: Path) -> List[Path]:
        """Find all Java source files."""
        src_dir = project_path / "src" / "main" / "java"
        return list(src_dir.rglob("*.java")) if src_dir.exists() else []
    
    def _generate_report(self) -> Dict:
        """Generate migration statistics report."""
        automation_rate = (
            self.results['files_migrated'] / self.results['files_processed'] * 100
            if self.results['files_processed'] > 0 else 0
        )
        
        self.results['automation_rate'] = automation_rate
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Pattern Migration Results:")
        logger.info(f"Files processed: {self.results['files_processed']}")
        logger.info(f"Files migrated: {self.results['files_migrated']}")
        logger.info(f"Automation rate: {automation_rate:.1f}%")
        logger.info(f"Total tokens used: {self.results['tokens_used']}")
        logger.info(f"\nBy pattern:")
        for pattern, stats in self.results['by_pattern'].items():
            logger.info(f"  {pattern}: {stats['success']} success, {stats['failed']} failed")
        logger.info(f"{'='*60}\n")
        
        return self.results
```

---

## Integration with mvp_migrator.py

Update your main migrator to use the orchestrator:

```python
# In mvp_migrator.py

from orchestrator import PatternOrchestrator

def run_migration_pipeline(project_path: Path) -> dict:
    """Execute full migration pipeline."""
    
    results = {
        'project': str(project_path),
        'phases': {}
    }
    
    # Phase 1: Analysis
    logger.info("Phase 1: Analyzing project")
    analysis = analyze_project(project_path)
    results['phases']['analysis'] = analysis
    
    # Phase 2: OpenRewrite
    logger.info("Phase 2: Running OpenRewrite")
    or_success, or_output = run_openrewrite(project_path, dry_run=False)
    results['phases']['openrewrite'] = {
        'success': or_success,
        'changes': parse_openrewrite_changes(or_output)
    }
    
    # Phase 3: Pattern-based Claude migrations (NEW)
    logger.info("Phase 3: Running pattern-based migrations")
    orchestrator = PatternOrchestrator()
    pattern_results = orchestrator.run(project_path)
    results['phases']['patterns'] = pattern_results
    
    # Phase 4: Validation
    logger.info("Phase 4: Validating compilation")
    compile_success, compile_output = validate_compilation(project_path)
    results['phases']['validation'] = {
        'compiles': compile_success,
        'output': compile_output
    }
    
    # Calculate overall automation rate
    openrewrite_changes = results['phases']['openrewrite']['changes']
    pattern_changes = pattern_results['files_migrated']
    total_changes = openrewrite_changes + pattern_changes
    
    results['automation_rate'] = (total_changes / 35) * 100  # Assuming 35 total changes needed
    results['tokens_used'] = pattern_results['tokens_used']
    
    return results
```

---

## Success Criteria

### Must Have:
- ✅ At least 3 pattern types implemented (Security, Config, Hibernate)
- ✅ Automation rate >70% on petclinic
- ✅ Token usage tracked per pattern
- ✅ Each pattern has 2+ test cases
- ✅ Orchestrator coordinates pattern detection
- ✅ Results report shows pattern breakdown

### Should Have:
- ✅ Prompt templates in separate files (reusable, versionable)
- ✅ Pattern-specific validation logic
- ✅ Graceful degradation (if one pattern fails, others continue)

### Nice to Have:
- ✅ JUnit 4→5 migration (if time permits)
- ✅ Metrics dashboard showing cost per pattern type
- ✅ Dry-run mode for pattern migrations

---

## Estimated Token Usage

**Per file:**
- Security advanced: ~3,000-4,000 tokens
- Config properties: ~1,500-2,000 tokens  
- Hibernate patterns: ~2,500-3,500 tokens

**For petclinic:**
- Estimated 5-8 files needing pattern migration
- Total: ~20,000-30,000 tokens
- Cost: ~$0.60-$0.90 at Sonnet 4.5 pricing

**For a 10K LOC module:**
- Estimated 30-50 files needing pattern migration
- Total: ~100,000-150,000 tokens
- Cost: ~$3.00-$4.50

---

## Testing Strategy

1. **Unit test each pattern migrator** with synthetic test cases
2. **Integration test** on petclinic (should increase automation from 49% to >70%)
3. **Validate** on real Spring Boot 2.7 project with Security + Hibernate
4. **Measure** token usage and cost per pattern type
5. **Document** patterns that work vs. patterns that need manual review

---

## Deliverables

At end of Phase 6:

1. ✅ `src/migration_patterns/` with 3+ pattern modules
2. ✅ `src/orchestrator.py` coordinating patterns
3. ✅ `prompts/` directory with reusable templates
4. ✅ `test-cases/` covering all patterns
5. ✅ Updated `mvp_migrator.py` using orchestrator
6. ✅ Test results showing >70% automation
7. ✅ Cost analysis per pattern type

---

## Next Steps After Phase 6

Once you hit >70% automation:

1. **Test on real monolith** (Phase 10) to find gaps
2. **Add retry logic** (Phase 7) for API failures
3. **Generate characterization tests** (Phase 8) for safety
4. **Consider LangGraph** (Phase 9) for stateful workflows

You'll have proven the core value proposition: **AI can automate the complex parts of Spring Boot migration that tools like OpenRewrite cannot.**
