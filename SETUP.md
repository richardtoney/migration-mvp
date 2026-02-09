# Arch Linux Development Environment Setup

## System Package Requirements

Install all required system packages before starting development:

```bash
# Java Development Kit (required for Maven and OpenRewrite)
sudo pacman -S jdk17-openjdk maven

# Python development environment
sudo pacman -S python python-pip python-virtualenv

# Git (for cloning test project)
sudo pacman -S git

# Optional but recommended: build tools
sudo pacman -S base-devel

# Verify installations
java -version        # Should show OpenJDK 17.x
mvn -version         # Should show Maven 3.6+
python --version     # Should show Python 3.11+
```

## Directory Structure

Create the complete project structure upfront:

```bash
# Create project root
mkdir -p ~/projects/migration-mvp
cd ~/projects/migration-mvp

# Create source structure
mkdir -p src tests docs

# Create test project directory
mkdir -p test-projects

# Your working structure should be:
# ~/projects/migration-mvp/
# ├── src/                      # Your Python code goes here
# ├── tests/                    # Unit tests (optional for MVP)
# ├── docs/                     # Documentation
# ├── test-projects/            # Cloned test applications
# ├── SPECIFICATION.md          # Project spec (create from artifact)
# ├── DEVELOPMENT_PLAN.md       # Phase plan (create from artifact)
# ├── requirements.txt          # Python dependencies
# ├── .env                      # Environment variables
# └── README.md                 # Project readme
```

## Python Virtual Environment Setup

```bash
cd ~/projects/migration-mvp

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
anthropic>=0.39.0
tree-sitter>=0.23.0
tree-sitter-java>=0.23.4
lxml>=5.1.0
requests>=2.31.0
python-dotenv>=1.0.0
EOF

# Install dependencies
pip install -r requirements.txt

# Verify anthropic SDK installation
python -c "import anthropic; print(anthropic.__version__)"
```

## Environment Variables

```bash
# Create .env file for API key and configuration
cat > .env << 'EOF'
# Anthropic API key (get from https://console.anthropic.com/)
ANTHROPIC_API_KEY=your_key_here

# Claude model to use
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Project paths
TEST_PROJECT_PATH=./test-projects/spring-petclinic
OPENREWRITE_VERSION=6.28.0

# Logging level
LOG_LEVEL=INFO
EOF

# IMPORTANT: Add your actual API key
nano .env  # or vim .env

# Add .env to .gitignore
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "test-projects/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

## Clone Test Project (Spring PetClinic)

```bash
cd ~/projects/migration-mvp/test-projects

# Clone official Spring PetClinic
git clone https://github.com/spring-projects/spring-petclinic.git

# Checkout and build the Spring Boot 2.7 commit
git checkout 9ecdc1111e3da388a750ace41a125287d9620534
mvn clean compile   # Verify it still builds

cd ~/projects/migration-mvp
```

## Verify OpenRewrite Works

Test that OpenRewrite can run against the test project:

```bash
cd ~/projects/migration-mvp/test-projects/spring-petclinic

# Run OpenRewrite in dry-run mode (no changes)
mvn -U org.openrewrite.maven:rewrite-maven-plugin:6.28.0:run \
  -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE \
  -Drewrite.activeRecipes=org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0 \
  -Drewrite.dryRun=true

# This should:
# 1. Download OpenRewrite plugin (first time only)
# 2. Analyze the project
# 3. Show planned changes in output
# 4. Exit with code 0

# If you see "Changes have been made", OpenRewrite is working correctly
# If you see errors about missing recipes, you may need to adjust the recipe coordinates
```

## Pre-Stage Reference Documentation

Download key reference materials to avoid rate limits during development:

```bash
cd ~/projects/migration-mvp/docs

# Spring Boot 3.0 Migration Guide
curl -o spring-boot-3-migration.md \
  https://raw.githubusercontent.com/spring-projects/spring-boot/main/UPGRADE.md

# OpenRewrite recipe documentation
curl -o openrewrite-spring-boot-3.md \
  "https://docs.openrewrite.org/recipes/java/spring/boot3/upgradespringboot_3_0"

# Spring Security 6 migration examples (manually save from browser)
# https://spring.io/blog/2022/02/21/spring-security-without-the-websecurityconfigureradapter

# Create a quick reference file with the Security migration pattern
cat > security-migration-example.md << 'EOF'
# Spring Security Migration Pattern

## Before (Spring Boot 2.x with WebSecurityConfigurerAdapter)
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/resources/**", "/webjars/**").permitAll()
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

## After (Spring Boot 3.x with SecurityFilterChain)
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers("/resources/**", "/webjars/**").permitAll()
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

## Key Changes
- No more extends WebSecurityConfigurerAdapter (removed in Spring Security 6)
- configure(HttpSecurity) becomes @Bean SecurityFilterChain
- authorizeRequests() → authorizeHttpRequests()
- antMatchers() → requestMatchers()
- Method chaining with .and() → Lambda DSL
- Must return http.build()
EOF
```

## Claude Code Token Management Strategies

### 1. **Set Budget Limits Upfront**

```bash
# Before starting Claude Code, set a context budget in your mind:
# - Each Claude Code iteration costs ~10-30K tokens
# - Sonnet 4.5 context window: 200K tokens
# - Budget for MVP: aim for <15 iterations = ~300K tokens total
# - At $3/$15 per million tokens, this is ~$1-5 for the entire MVP

# Monitor usage in real-time:
# - Check https://console.anthropic.com/settings/usage
# - Claude Code shows token usage after each response
```

### 2. **Minimize Context Pollution**

```bash
# Keep your working directory clean - Claude Code reads everything
cd ~/projects/migration-mvp

# Only include necessary files in the working directory
# DO NOT have Claude Code work directly in test-projects/spring-petclinic
# (it will index thousands of Java files unnecessarily)

# Good structure:
migration-mvp/
├── src/              # Only your Python code here
├── SPECIFICATION.md  # < 5KB
├── DEVELOPMENT_PLAN.md  # < 3KB
└── requirements.txt  # < 1KB

# Bad structure (avoid):
migration-mvp/
├── test-projects/spring-petclinic/  # 50MB of Java code!
```

### 3. **Use Explicit Phase Gates**

```bash
# Start Claude Code with phase-locked instructions:

claude-code "Read SPECIFICATION.md and DEVELOPMENT_PLAN.md.

Execute ONLY Phase 1. After completing Phase 1, STOP and wait 
for my explicit approval before proceeding to Phase 2.

Do not read files in test-projects/ unless I explicitly tell you to.
All code should go in src/ directory."

# This prevents runaway token usage from Claude Code trying to 
# "be helpful" by reading the entire test project
```

### 4. **Provide Examples Inline, Not By Reference**

```bash
# EXPENSIVE (forces Claude Code to read external files):
"Read the Spring Security example from docs/security-migration-example.md 
and implement the migration"

# CHEAP (example is already in context via SPECIFICATION.md):
"Implement the Spring Security migration as specified in SPECIFICATION.md 
section 'Reference Materials - Spring Security Pattern'"
```

### 5. **Use Dry-Run Mode for Validation**

```bash
# When validating OpenRewrite integration, use dry-run to avoid
# actually modifying files Claude Code might then try to read/analyze

# In your spec, tell Claude Code:
"For validation, always use OpenRewrite in dry-run mode:
  -Drewrite.dryRun=true
This prevents file modification that would require re-indexing."
```

### 6. **Checkpoint and Reset**

```bash
# If Claude Code gets stuck in a loop:

# 1. Stop the current session
Ctrl+C in Claude Code

# 2. Save current progress
cp -r src src.backup

# 3. Review what worked
git status
git diff

# 4. Restart with narrower scope
claude-code "Continue from Phase 2, Task 3 only. 
Previous context: [paste 2-3 sentence summary].
Do not re-read completed files."

# 5. If totally stuck, reset:
git checkout -- .
# Restart with refined SPECIFICATION.md based on what you learned
```

### 7. **Monitor for Token Waste Patterns**

**Red flags that Claude Code is wasting tokens:**
- Repeatedly reading the same file without making progress
- Asking to "review all Java files" in test-projects/
- Generating >500 lines of code in a single response for MVP scope
- Re-implementing functionality that already exists in libraries

**How to intervene:**
```bash
# Mid-session correction:
"STOP. You are reading too many files. 

Focus only on src/openrewrite_runner.py. 
Do not read any files in test-projects/.
Do not read requirements.txt again.

Task: Fix the subprocess call to OpenRewrite. 
Show me only the run_openrewrite() function."
```

### 8. **Use .claudeignore**

```bash
# Create a .claudeignore file (like .gitignore for Claude Code)
cat > .claudeignore << 'EOF'
test-projects/
venv/
*.pyc
__pycache__/
.git/
*.log
*.class
target/
EOF

# This prevents Claude Code from indexing these directories
```

## Pre-Flight Checklist

Before starting development with Claude Code, verify:

```bash
# 1. Java and Maven work
java -version && mvn -version

# 2. Python environment is activated
which python  # Should show ~/projects/migration-mvp/venv/bin/python

# 3. Dependencies are installed
python -c "import anthropic, tree_sitter"

# 4. API key is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API key loaded' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING KEY')"

# 5. Test project builds
cd test-projects/spring-petclinic && mvn clean compile && cd ../..

# 6. OpenRewrite can run
cd test-projects/spring-petclinic && \
  mvn org.openrewrite.maven:rewrite-maven-plugin:6.28.0:dryRun \
  -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE \
  -Drewrite.activeRecipes=org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0 && \
  cd ../..

# 7. Specification files are in place
ls -lh SPECIFICATION.md DEVELOPMENT_PLAN.md

# If all checks pass, you're ready to start Claude Code
```

## Starting Claude Code Session

```bash
# Activate virtual environment
cd ~/projects/migration-mvp
source venv/bin/activate

# Start Claude Code with clear boundaries
claude-code "Hello! I need you to build a Spring Boot migration tool.

BEFORE WRITING ANY CODE:
1. Read SPECIFICATION.md completely
2. Read DEVELOPMENT_PLAN.md completely
3. Confirm you understand the mission and constraints

THEN execute Phase 1 ONLY. Stop after Phase 1 validation.

IMPORTANT: Do not read any files in test-projects/ directory 
unless I explicitly tell you to. All your code goes in src/."

# From this point, let Claude Code work through the phases
# Review and approve each phase before allowing it to continue
```

## Troubleshooting Common Issues

### OpenRewrite fails with "Unable to find recipe"
```bash
# Solution: Use explicit recipe coordinates
-Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE
```

### Maven fails with "JAVA_HOME not set"
```bash
# Solution: Set JAVA_HOME explicitly
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk' >> ~/.bashrc
```

### tree-sitter fails to parse Java
```bash
# Rebuild tree-sitter language bindings
pip uninstall tree-sitter tree-sitter-java
pip install --no-cache-dir tree-sitter tree-sitter-java
```

### Claude Code runs out of context
```bash
# Use the checkpoint strategy above
# OR simplify SPECIFICATION.md - remove verbose examples
# OR process one file at a time instead of batching
```

## Estimated Resource Usage

**Disk space:**
- Virtual environment: ~500MB
- Test project (spring-petclinic): ~50MB
- Maven local repository (first build): ~200MB
- Total: ~750MB

**Memory:**
- Maven build: ~1-2GB
- Python + Claude Code: ~500MB
- Total: <3GB

**API costs for MVP (estimated):**
- Phase 1-2: ~50K tokens (~$0.15)
- Phase 3: ~150K tokens (~$0.50)
- Phase 4: ~100K tokens (~$0.30)
- Total: ~$1-2 if executed efficiently

**Time:**
- Setup (this file): 30 minutes
- Claude Code development: 6 hours
- Your review/iteration: 1.5 hours
- Total: ~8 hours

## Next Steps

1. Complete this setup checklist
2. Create SPECIFICATION.md from provided artifact
3. Create DEVELOPMENT_PLAN.md from provided artifact
4. Run pre-flight checklist
5. Start Claude Code with Phase 1
6. Review each phase before proceeding
7. Document results and decide on full build

Good luck! You're now ready to start development.

