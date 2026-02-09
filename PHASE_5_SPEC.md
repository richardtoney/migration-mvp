# Phase 5: Validate Claude Integration with Real Security Configs

## Overview
**Goal:** Prove Claude can migrate WebSecurityConfigurerAdapter → SecurityFilterChain patterns since petclinic had no security configs to test against.

**Time estimate:** 4-6 hours  
**Priority:** CRITICAL - You built capability without validating it works

---

## Architecture Additions

### New Files to Create
```
migration-mvp/
├── test-projects/
│   ├── spring-petclinic/              # Existing
│   └── security-test-apps/            # NEW
│       ├── basic-security/            # Simple form login
│       ├── oauth2-security/           # OAuth2 client config
│       └── custom-filters/            # Custom security filters
├── src/
│   └── pattern_validators/           # NEW
│       ├── __init__.py
│       └── security_validator.py     # Validates Security migrations
└── test-cases/                        # NEW
    └── security_configs/              # Synthetic test cases
        ├── basic_form_auth.java
        ├── method_security.java
        └── custom_authentication.java
```

---

## Task 1: Create Synthetic Security Test Cases (1-2 hours)

### 1.1 Create test-cases/security_configs/ directory

```bash
mkdir -p ~/projects/migration-mvp/test-cases/security_configs
```

### 1.2 Create basic_form_auth.java

This represents the most common pattern:

```java
package org.example.security;

import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;

@Configuration
@EnableWebSecurity
public class BasicSecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/", "/public/**").permitAll()
                .antMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            .and()
            .formLogin()
                .loginPage("/login")
                .permitAll()
            .and()
            .logout()
                .permitAll();
    }
}
```

**Expected migration:**
```java
package org.example.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class BasicSecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers("/", "/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .permitAll()
            )
            .logout(logout -> logout
                .permitAll()
            );
        return http.build();
    }
}
```

### 1.3 Create method_security.java

Tests @PreAuthorize and method-level security:

```java
package org.example.security;

import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true, securedEnabled = true)
public class MethodSecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .anyRequest().authenticated()
            .and()
            .httpBasic();
    }
}
```

**Expected migration:**
```java
package org.example.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true, securedEnabled = true)
public class MethodSecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authorize -> authorize
                .anyRequest().authenticated()
            )
            .httpBasic(Customizer.withDefaults());
        return http.build();
    }
}
```

### 1.4 Create csrf_and_cors.java

Tests CSRF and CORS configuration:

```java
package org.example.security;

import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;

@Configuration
@EnableWebSecurity
public class CsrfCorsConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .anyRequest().authenticated()
            .and()
            .csrf()
                .ignoringAntMatchers("/api/**")
            .and()
            .cors();
    }
}
```

---

## Task 2: Enhance claude_fixer.py to Handle Edge Cases (1-2 hours)

### 2.1 Update migrate_security_config() to handle variations

Current implementation likely handles the happy path. Add:

**Edge cases to handle:**
1. Multiple `configure()` methods (HttpSecurity, WebSecurity)
2. `@EnableGlobalMethodSecurity` → `@EnableMethodSecurity`
3. Custom filters added via `.addFilterBefore()` or `.addFilterAfter()`
4. Session management configuration
5. Remember-me configuration
6. Custom authentication providers

### 2.2 Add validation function

```python
def validate_security_migration(original_file: Path, migrated_code: str) -> tuple[bool, List[str]]:
    """
    Validate that migrated Security config preserves all rules.
    
    Returns:
        (is_valid: bool, issues: List[str])
    """
    issues = []
    
    # Read original file
    original_code = original_file.read_text()
    
    # Check 1: All antMatchers converted to requestMatchers
    if 'antMatchers' in original_code and 'requestMatchers' not in migrated_code:
        issues.append("antMatchers not converted to requestMatchers")
    
    # Check 2: Has @Bean SecurityFilterChain
    if '@Bean' not in migrated_code or 'SecurityFilterChain' not in migrated_code:
        issues.append("Missing @Bean SecurityFilterChain")
    
    # Check 3: Has return http.build()
    if 'return http.build()' not in migrated_code:
        issues.append("Missing return http.build()")
    
    # Check 4: No more extends WebSecurityConfigurerAdapter
    if 'extends WebSecurityConfigurerAdapter' in migrated_code:
        issues.append("Still extends WebSecurityConfigurerAdapter")
    
    # Check 5: authorizeRequests → authorizeHttpRequests
    if 'authorizeRequests' in migrated_code:
        issues.append("Still using authorizeRequests instead of authorizeHttpRequests")
    
    # Check 6: Lambda DSL used (no .and())
    and_count = migrated_code.count('.and()')
    if and_count > 0:
        issues.append(f"Still using .and() chaining ({and_count} occurrences)")
    
    return len(issues) == 0, issues
```

### 2.3 Update Claude prompt template

Enhance your existing prompt with more specific instructions:

```python
SECURITY_MIGRATION_PROMPT_ENHANCED = """You are migrating Spring Security configuration from Spring Boot 2.x to Spring Boot 3.x.

CRITICAL RULES:
1. Remove 'extends WebSecurityConfigurerAdapter'
2. Change method signature: protected void configure(HttpSecurity http) → @Bean public SecurityFilterChain filterChain(HttpSecurity http)
3. Replace all .antMatchers() with .requestMatchers()
4. Replace .authorizeRequests() with .authorizeHttpRequests(authorize -> ...)
5. Convert method chaining with .and() to lambda DSL
6. Add 'return http.build();' at the end
7. If @EnableGlobalMethodSecurity exists, change to @EnableMethodSecurity
8. Import org.springframework.security.web.SecurityFilterChain
9. Import org.springframework.security.config.Customizer if using .withDefaults()

PRESERVE:
- All security rules (permitAll, hasRole, etc.)
- All URL patterns exactly as-is
- Login page configurations
- Logout configurations
- CSRF settings
- CORS settings
- Custom filters
- Session management

Here is the original Spring Security configuration:

```java
{original_code}
```

Return ONLY the migrated Java code with no explanations, no markdown formatting, no preamble.
"""
```

---

## Task 3: Create Security Validator Module (1 hour)

### 3.1 Create src/pattern_validators/security_validator.py

```python
"""
Validates Spring Security configuration migrations.
"""
from pathlib import Path
from typing import List, Tuple
import re


class SecurityMigrationValidator:
    """Validates Security config migrations preserve behavior."""
    
    def __init__(self):
        self.required_changes = [
            ("extends WebSecurityConfigurerAdapter", "removed"),
            ("@Bean", "added"),
            ("SecurityFilterChain", "added"),
            ("return http.build()", "added"),
        ]
    
    def validate(self, original: str, migrated: str) -> Tuple[bool, List[str]]:
        """
        Validate migration preserves security rules.
        
        Returns:
            (is_valid, issues)
        """
        issues = []
        
        # Extract security rules from original
        original_rules = self._extract_security_rules(original)
        migrated_rules = self._extract_security_rules(migrated)
        
        # Check all rules preserved
        for rule in original_rules:
            if rule not in migrated_rules:
                issues.append(f"Security rule lost: {rule}")
        
        # Check required transformations
        if "extends WebSecurityConfigurerAdapter" in migrated:
            issues.append("Still extends WebSecurityConfigurerAdapter")
        
        if "antMatchers" in migrated:
            issues.append("antMatchers not converted to requestMatchers")
        
        if "authorizeRequests()" in migrated:
            issues.append("authorizeRequests not converted to authorizeHttpRequests")
        
        if "@Bean" not in migrated or "SecurityFilterChain" not in migrated:
            issues.append("Missing @Bean SecurityFilterChain")
        
        if "return http.build()" not in migrated:
            issues.append("Missing return http.build()")
        
        # Check lambda DSL (should have minimal .and())
        and_count = migrated.count(".and()")
        if and_count > 2:  # Allow some .and() for complex configs
            issues.append(f"Excessive .and() chaining: {and_count} occurrences")
        
        return len(issues) == 0, issues
    
    def _extract_security_rules(self, code: str) -> List[str]:
        """Extract security rules like permitAll, hasRole, etc."""
        rules = []
        
        # Match patterns like .antMatchers("/admin/**").hasRole("ADMIN")
        patterns = [
            r'\.(antMatchers|requestMatchers)\([^)]+\)\.\w+\([^)]*\)',
            r'\.permitAll\(\)',
            r'\.hasRole\([^)]+\)',
            r'\.hasAnyRole\([^)]+\)',
            r'\.authenticated\(\)',
            r'\.denyAll\(\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            rules.extend(matches)
        
        return rules


def compile_java_file(file_path: Path) -> Tuple[bool, str]:
    """
    Compile a single Java file to validate syntax.
    
    Returns:
        (success, error_message)
    """
    import subprocess
    
    # Create a temporary directory with minimal Spring Boot structure
    # This is simplified - real implementation would need proper classpath
    result = subprocess.run(
        ["javac", str(file_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return True, ""
    else:
        return False, result.stderr
```

---

## Task 4: Create Test Runner Script (1 hour)

### 4.1 Create test_security_migrations.py

```python
#!/usr/bin/env python3
"""
Test runner for Security configuration migrations.
Validates Claude can correctly migrate various Security patterns.
"""
from pathlib import Path
import sys
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_fixer import migrate_security_config
from pattern_validators.security_validator import SecurityMigrationValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_security_migration(test_file: Path, validator: SecurityMigrationValidator):
    """Test migration of a single security config file."""
    logger.info(f"Testing: {test_file.name}")
    
    # Read original
    original_code = test_file.read_text()
    
    # Migrate
    success, migrated_code, tokens_used = migrate_security_config(test_file)
    
    if not success:
        logger.error(f"❌ Migration failed: {migrated_code}")
        return False
    
    # Validate
    is_valid, issues = validator.validate(original_code, migrated_code)
    
    if is_valid:
        logger.info(f"✅ Migration valid ({tokens_used} tokens)")
        return True
    else:
        logger.error(f"❌ Validation failed:")
        for issue in issues:
            logger.error(f"   - {issue}")
        logger.info(f"\nMigrated code:\n{migrated_code}\n")
        return False


def main():
    """Run all security migration tests."""
    test_dir = Path("test-cases/security_configs")
    
    if not test_dir.exists():
        logger.error(f"Test directory not found: {test_dir}")
        sys.exit(1)
    
    test_files = list(test_dir.glob("*.java"))
    
    if not test_files:
        logger.error(f"No test files found in {test_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(test_files)} test files")
    
    validator = SecurityMigrationValidator()
    results = []
    
    for test_file in test_files:
        result = test_security_migration(test_file, validator)
        results.append((test_file.name, result))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Results: {passed}/{total} passed")
    logger.info(f"{'='*60}")
    
    for name, result in results:
        status = "✅" if result else "❌"
        logger.info(f"{status} {name}")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
```

---

## Task 5: Test with Real Projects (1-2 hours)

After validating synthetic cases, test against real Spring Boot 2.7 projects with Security. See separate "Test Projects" document for curated list.

### 5.1 Clone test project

```bash
cd ~/projects/migration-mvp/test-projects/security-test-apps
git clone <project-url>
cd <project-name>
```

### 5.2 Run your migrator

```bash
cd ~/projects/migration-mvp
python src/mvp_migrator.py --project-path ./test-projects/security-test-apps/<project-name>
```

### 5.3 Analyze results

**Check:**
- How many Security configs were found?
- How many migrated successfully?
- Token usage per config
- Compilation success rate
- Any patterns Claude struggled with?

---

## Success Criteria

### Must Have:
- ✅ At least 3 different Security config patterns migrate successfully
- ✅ All migrated configs compile (parse as valid Java)
- ✅ Validation detects when rules are lost or incorrect
- ✅ Token usage reasonable (<5K per config)
- ✅ Test runner passes 100% on synthetic test cases

### Should Have:
- ✅ Tested against 2+ real open-source projects
- ✅ Success rate >80% on real projects
- ✅ Issues documented for patterns that fail

### Nice to Have:
- ✅ Automated regression test suite
- ✅ Benchmark of token usage across pattern types
- ✅ Gallery of before/after examples

---

## Metrics to Track

Create a spreadsheet or JSON file tracking:

```json
{
  "test_cases": [
    {
      "name": "basic_form_auth.java",
      "tokens_used": 2847,
      "success": true,
      "validation_passed": true,
      "compilation_passed": true,
      "time_seconds": 3.2
    },
    {
      "name": "method_security.java",
      "tokens_used": 3104,
      "success": true,
      "validation_passed": true,
      "compilation_passed": true,
      "time_seconds": 3.8
    }
  ],
  "real_projects": [
    {
      "name": "spring-boot-security-jwt",
      "configs_found": 2,
      "configs_migrated": 2,
      "tokens_used": 6203,
      "success_rate": 1.0,
      "issues": []
    }
  ],
  "summary": {
    "total_configs_tested": 5,
    "success_rate": 1.0,
    "avg_tokens_per_config": 3241,
    "total_cost_usd": 0.15
  }
}
```

---

## Common Issues and Solutions

### Issue 1: Claude returns incomplete code
**Solution:** Update prompt to explicitly say "Return the COMPLETE class including all imports, annotations, and the closing brace."

### Issue 2: Lambda syntax varies
**Solution:** Show 2-3 examples of lambda syntax in prompt. Claude learns from examples.

### Issue 3: Custom authentication providers lost
**Solution:** Add explicit instruction: "If the original has @Bean methods for AuthenticationProvider, UserDetailsService, or PasswordEncoder, preserve them exactly."

### Issue 4: Token usage too high
**Solution:** Only send the Security config class to Claude, not entire file. Extract just the class with tree-sitter.

---

## Next Steps After Phase 5

Once you have confidence Claude works on Security configs:

1. **Document patterns** - Create a reference of what works
2. **Build pattern library** - Reusable prompts for common variations
3. **Move to Phase 6** - Add more migration patterns
4. **Update success criteria** - You can now mark criterion #2 as ✅

---

## Deliverables

At the end of Phase 5, you should have:

1. ✅ `test-cases/security_configs/` with 3+ synthetic test cases
2. ✅ `src/pattern_validators/security_validator.py` - Validation logic
3. ✅ `test_security_migrations.py` - Test runner
4. ✅ Updated `claude_fixer.py` with enhanced prompts
5. ✅ Metrics JSON file with test results
6. ✅ Documentation of what works and what doesn't
7. ✅ At least 2 real projects tested successfully

This validates your core value proposition: **Claude can handle complex pattern migrations that OpenRewrite cannot.**
