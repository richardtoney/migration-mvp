# Test Projects Guide: Spring Boot 2.7 Migration Validation

## Purpose

This document provides a curated list of open-source Spring Boot 2.7 projects to test your migration agent against. Projects are organized by complexity, patterns present, and testing value.

---

## Testing Strategy

### Progressive Complexity Approach

1. **Tier 1: Foundational** (Phase 5) - Simple apps with specific patterns
2. **Tier 2: Intermediate** (Phase 6-7) - Realistic apps with multiple patterns
3. **Tier 3: Enterprise** (Phase 10) - Large, complex systems closer to your monoliths

### What to Track for Each Project

```json
{
  "project_name": "...",
  "spring_boot_version": "2.7.x",
  "loc": 5000,
  "patterns_present": ["Security", "JPA", "REST"],
  "migration_results": {
    "openrewrite_changes": 42,
    "claude_migrations": 8,
    "total_files": 120,
    "automation_rate": 0.73,
    "tokens_used": 45000,
    "cost_usd": 1.35,
    "manual_fixes": 12,
    "compilation_success": true,
    "tests_passing": 0.85
  }
}
```

---

## TIER 1: FOUNDATIONAL TEST PROJECTS

### 1.1 Spring PetClinic (BASELINE - ALREADY TESTED)

**Why use it:**
- Official Spring sample app
- Well-documented, good test coverage
- Realistic complexity (~5K LOC)
- Known baseline: 49% automation in your MVP

**Project details:**
```
Repository: https://github.com/spring-projects/spring-petclinic
Commit: 9ecdc1111e3da388a750ace41a125287d9620534
Spring Boot: 2.7.4
LOC: ~5,000
```

**Patterns present:**
- Spring Data JPA
- Spring MVC
- Thymeleaf templates
- H2 database
- Spring Boot Actuator
- **No Spring Security** (limitation discovered in Phase 5)

**Clone command:**
```bash
cd ~/projects/migration-mvp/test-projects
git clone https://github.com/spring-projects/spring-petclinic.git petclinic-baseline
cd petclinic-baseline
git checkout 9ecdc1111e3da388a750ace41a125287d9620534
```

---

### 1.2 Spring Boot RealWorld Example (RECOMMENDED FOR PHASE 5)

**Why use it:**
- Real-world REST API patterns
- **HAS Spring Security with JWT** (validates Phase 5)
- Authentication & authorization
- CORS configuration

**Project details:**
```
Repository: https://github.com/gothinkster/spring-boot-realworld-example-app
Branch: master
Spring Boot: ~2.6-2.7 (check pom.xml)
LOC: ~3,000
```

**Patterns present:**
- ✅ WebSecurityConfigurerAdapter (CRITICAL for Phase 5)
- JWT token generation
- Custom filters (JwtTokenFilter)
- CORS configuration
- Spring Data JPA
- H2 database
- REST API

**Migration complexity:** MEDIUM
- Security config migration essential
- Custom authentication flow
- JWT integration may need attention

**Clone command:**
```bash
cd ~/projects/migration-mvp/test-projects
git clone https://github.com/gothinkster/spring-boot-realworld-example-app.git realworld-jwt
cd realworld-jwt
mvn clean compile  # Verify it builds
```

**Expected validation:**
- Security config should migrate cleanly
- JWT generation logic preserved
- Custom filters maintained
- CORS config updated to lambda DSL

---

### 1.3 Spring Boot OAuth2 JWT Example

**Why use it:**
- OAuth2 authorization server + resource server
- Advanced Security patterns
- JWT token store

**Project details:**
```
Repository: https://github.com/JavaChinna/spring-boot-oauth2-jwt
Branch: master
Spring Boot: 2.x
LOC: ~4,000
```

**Patterns present:**
- OAuth2 authorization configuration
- JWT token customization
- Multiple Security configs
- Role-based access control
- Spring Data JPA

**Migration complexity:** HIGH
- OAuth2 autoconfiguration changed significantly in Spring Boot 3.x
- May require significant manual intervention
- Good test of Claude's limits

**Clone command:**
```bash
cd ~/projects/migration-mvp/test-projects
git clone https://github.com/JavaChinna/spring-boot-oauth2-jwt.git oauth2-jwt
cd oauth2-jwt
# Check Spring Boot version in pom.xml, may need to find 2.7 tag
```

---

## TIER 2: INTERMEDIATE COMPLEXITY

### 2.1 eladmin (HIGHLY RECOMMENDED - CLOSEST TO YOUR MONOLITHS)

**Why use it:**
- Enterprise admin system (20K+ stars)
- **Spring Boot 2.7.18** (exact version)
- Multi-module structure
- RBAC permissions
- Production-grade patterns

**Project details:**
```
Repository: https://github.com/elunez/eladmin
Branch: master
Spring Boot: 2.7.18
LOC: ~25,000
Modules: 4 (common, system, logging, tools, generator)
```

**Patterns present:**
- ✅ Spring Security with JWT
- ✅ Custom authentication provider
- Spring Data JPA with complex queries
- Redis integration
- Email service
- File storage (local + S3-compatible)
- Alipay payment integration
- Code generator module
- Scheduled tasks (@Scheduled)
- Custom annotations and AOP
- Druid connection pool
- MapStruct DTOs

**Migration complexity:** HIGH
- Multi-module requires coordinated migration
- Custom security with JWT
- Third-party integrations
- Redis session management
- **Great test of real-world complexity**

**Clone command:**
```bash
cd ~/projects/migration-mvp/test-projects
git clone https://github.com/elunez/eladmin.git eladmin
cd eladmin
mvn clean compile  # Should build on Spring Boot 2.7.18
```

**Why this is valuable:**
- Closest to enterprise monolith structure
- Tests multi-module migration
- Complex Security configuration
- Third-party library compatibility
- **If your tool can handle eladmin, it can handle production monoliths**

---

### 2.2 Spring Boot + PostgreSQL JPA REST API

**Why use it:**
- PostgreSQL dialect migration testing
- REST API patterns
- Good documentation

**Project details:**
```
Repository: https://github.com/callicoder/spring-boot-postgresql-jpa-hibernate-rest-api-demo
Branch: master
Spring Boot: 2.x
LOC: ~1,500
```

**Patterns present:**
- PostgreSQL9Dialect → PostgreSQLDialect migration
- Spring Data JPA
- REST controllers
- Exception handling
- CORS

**Migration complexity:** MEDIUM
- Simpler than eladmin
- Tests Hibernate dialect changes
- Clean REST patterns

**Clone command:**
```bash
cd ~/projects/migration-mvp/test-projects
git clone https://github.com/callicoder/spring-boot-postgresql-jpa-hibernate-rest-api-demo.git postgres-rest
```

---

### 2.3 Spring Boot Warehouse API (QueryDSL + Flyway)

**Why use it:**
- QueryDSL integration (may need migration)
- Flyway database migrations
- DTO patterns
- Clean architecture

**Project details:**
```
Repository: https://github.com/elenamountz/spring-boot-rest-api-warehouse
Branch: master
Spring Boot: 2.x
LOC: ~3,500
```

**Patterns present:**
- QueryDSL for dynamic queries
- Flyway migrations
- DTO/Entity separation with ModelMapper
- MySQL
- RESTful design

**Migration complexity:** MEDIUM-HIGH
- QueryDSL may need dependency updates
- Flyway should be compatible
- Tests DTO mapping patterns

**Clone command:**
```bash
cd ~/projects/migration-mvp/test-projects
git clone https://github.com/elenamountz/spring-boot-rest-api-warehouse.git warehouse-querydsl
```

---

## TIER 3: ENTERPRISE COMPLEXITY

### 3.1 Spring Security OAuth2 Separate Services

**Why use it:**
- Microservices architecture
- Separate auth server + resource server
- Complex OAuth2 flow

**Project details:**
```
Repository: https://github.com/melardev/JavaSpringBootOAuth2AsymmetricJwt_Separate_Crud
Branch: master
Spring Boot: 2.x
LOC: ~10,000+ (multiple services)
```

**Patterns present:**
- Asymmetric JWT (RSA keys)
- Authorization server
- Resource server
- Client credentials flow
- Password grant flow
- Spring Data JPA
- Pagination

**Migration complexity:** VERY HIGH
- Multi-service coordination
- OAuth2 changes significant in Spring Boot 3.x
- RSA key handling
- **Tests limits of automated migration**

**Clone command:**
```bash
cd ~/projects/migration-mvp/test-projects
git clone https://github.com/melardev/JavaSpringBootOAuth2AsymmetricJwt_Separate_Crud.git oauth2-microservices
```

---

## SPECIAL PURPOSE TEST PROJECTS

### SP.1 Spring Boot + Hibernate Custom Types

**Purpose:** Test Hibernate 6 migration specifically

**Create synthetic project:**
```bash
mkdir -p ~/projects/migration-mvp/test-projects/hibernate-custom-types
# Create entities with:
# - @Type(type = "json")
# - @Type(type = "uuid-char")
# - Custom UserType implementations
# - MySQL5Dialect in application.properties
```

**Patterns to include:**
```java
// JSON type
@Type(type = "json")
@Column(columnDefinition = "json")
private Map<String, Object> metadata;

// UUID as char
@Type(type = "uuid-char")
private UUID identifier;

// Custom dialect
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MySQL5InnoDBDialect
```

---

### SP.2 Spring Boot Configuration Properties Showcase

**Purpose:** Test application.properties migration

**Create synthetic application.properties:**
```properties
# Deprecated in Spring Boot 3.x
server.error.whitelabel.enabled=true
spring.http.log-request-details=true
spring.jpa.hibernate.use-new-id-generator-mappings=true
management.metrics.export.prometheus.enabled=true

# Actuator exposure
management.endpoints.web.exposure.include=*

# Data source
spring.datasource.url=jdbc:mysql://localhost:3306/test
spring.datasource.driver-class-name=com.mysql.jdbc.Driver
```

---

## TESTING CHECKLIST BY PHASE

### Phase 5: Validate Claude with Security Configs

**Test on:**
1. ✅ Synthetic test cases (basic_form_auth.java, etc.)
2. ✅ spring-boot-realworld-example-app (has WebSecurityConfigurerAdapter)
3. ✅ spring-boot-oauth2-jwt (advanced Security)

**Success criteria:**
- All synthetic cases migrate correctly
- RealWorld app Security config migrates
- OAuth2 app handled or documented as limitation

---

### Phase 6: Add More Patterns

**Test on:**
1. ✅ PetClinic (baseline comparison)
2. ✅ eladmin (multi-pattern complexity)
3. ✅ postgres-rest (Hibernate dialect changes)
4. ✅ warehouse-querydsl (QueryDSL compatibility)

**Success criteria:**
- Automation rate >70% on at least 2 projects
- All pattern types exercised
- Token usage reasonable (<$5 per project)

---

### Phase 7-8: Retry Logic + Characterization Tests

**Test on:**
1. ✅ eladmin (complex enough to trigger errors)
2. ✅ oauth2-microservices (multi-service failures)

**Success criteria:**
- API failures gracefully retried
- Characterization tests generated
- Tests pass pre- and post-migration

---

### Phase 10: Real Monolith Testing

**Test on:**
1. Your actual FDA monoliths (pilot module)
2. eladmin full migration
3. Large open-source project (>50K LOC)

**Success criteria:**
- >70% automation on real monolith
- Manual fixes documented
- Cost per LOC calculated
- Team can use the tool

---

## PROJECT COMPARISON MATRIX

| Project | Spring Boot | LOC | Security | Hibernate | Multi-Module | Complexity | Phase |
|---------|-------------|-----|----------|-----------|--------------|------------|-------|
| PetClinic | 2.7.4 | 5K | ❌ | ✅ | ❌ | Low | MVP |
| RealWorld | 2.6-2.7 | 3K | ✅ JWT | ✅ | ❌ | Medium | 5 |
| OAuth2-JWT | 2.x | 4K | ✅ OAuth2 | ✅ | ❌ | High | 5 |
| eladmin | 2.7.18 | 25K | ✅ Custom | ✅ | ✅ | High | 6 |
| Postgres-REST | 2.x | 1.5K | ❌ | ✅ Postgres | ❌ | Medium | 6 |
| Warehouse | 2.x | 3.5K | ❌ | ✅ QueryDSL | ❌ | Medium | 6 |
| OAuth2-Micro | 2.x | 10K+ | ✅ Complex | ✅ | ✅ | Very High | 10 |

---

## METRICS TO TRACK

For each test project, record:

**Before migration:**
- Spring Boot version
- Dependencies with versions
- Number of Security configs
- Number of JPA entities
- Configuration files count
- Test count and coverage

**After migration:**
- OpenRewrite changes applied
- Claude pattern migrations
- Total files modified
- Compilation success (yes/no)
- Test pass rate
- Application starts (yes/no)
- Manual fixes required
- Tokens used
- Cost in USD
- Time taken (minutes)

**Quality metrics:**
- Automation rate: (automated_changes / total_changes)
- Cost per file: (total_cost / files_modified)
- Cost per LOC: (total_cost / total_lines_of_code)
- Success rate: (successful_migrations / attempted_migrations)

---

## RECOMMENDED TESTING SEQUENCE

### Week 1: Phase 5 (Security Validation)
1. Synthetic Security test cases
2. RealWorld app (JWT + Security)
3. Document what works

### Week 2: Phase 6 (Pattern Expansion)
1. Re-test PetClinic (baseline improvement)
2. eladmin (comprehensive patterns)
3. Postgres-REST (Hibernate dialects)
4. Measure automation rate >70%

### Week 3: Phase 7-8 (Hardening)
1. eladmin with retry logic
2. Characterization test generation
3. Error recovery testing

### Week 4: Phase 10 (Production Validation)
1. Small FDA monolith module
2. Full eladmin migration
3. Cost/benefit analysis
4. Handoff to team

---

## WHERE TO FIND MORE TEST PROJECTS

### GitHub Search Queries

**Spring Boot 2.7 with Security:**
```
language:java "spring-boot-starter-parent" "2.7" WebSecurityConfigurerAdapter
```

**Spring Boot 2.7 with JPA:**
```
language:java "spring-boot-starter-parent" "2.7" "spring-boot-starter-data-jpa"
```

**Enterprise examples:**
```
stars:>1000 language:java spring-boot "2.7"
```

### Additional Resources

- **Baeldung tutorials:** Often have Spring Boot 2.7 examples
- **Official Spring guides:** https://spring.io/guides (check for 2.7 tags)
- **Awesome Spring Boot:** https://github.com/stunstunstun/awesome-spring-boot

---

## NOTES ON PROJECT SELECTION

**Good test projects have:**
- ✅ Spring Boot 2.7.x (exact version match)
- ✅ Maven build (your tool uses Maven)
- ✅ Compiles successfully on 2.7
- ✅ Multiple migration patterns present
- ✅ Active maintenance (recent commits)
- ✅ Good README/documentation

**Avoid:**
- ❌ Unmaintained projects (>2 years old)
- ❌ Gradle-only builds (unless you add Gradle support)
- ❌ Broken builds on Spring Boot 2.7
- ❌ No clear migration path to 3.x
- ❌ Experimental/POC code

---

## SUCCESS METRICS BY PROJECT TYPE

**Simple project (PetClinic-level):**
- Target: >70% automation
- Budget: <5,000 tokens (~$0.15)
- Time: <5 minutes

**Medium project (eladmin-level):**
- Target: >60% automation
- Budget: <50,000 tokens (~$1.50)
- Time: <30 minutes

**Large project (monolith module):**
- Target: >50% automation
- Budget: <200,000 tokens (~$6.00)
- Time: <2 hours

---

## FINAL RECOMMENDATION

**For Phase 5 (Security validation):**
→ Use **spring-boot-realworld-example-app** (has real Security configs)

**For Phase 6 (Pattern expansion):**
→ Use **eladmin** (comprehensive, realistic, Spring Boot 2.7.18)

**For Phase 10 (Production readiness):**
→ Use actual **FDA monolith module** (proves business value)

These three projects will give you high confidence that your migration agent works on production code, not just samples.
