"""
Validates Spring Security configuration migrations.
Checks that migrated code uses Boot 3.x patterns and preserves all security rules.
"""

import re


class SecurityMigrationValidator:
    """Validates Security config migrations preserve behavior."""

    def validate(self, original: str, migrated: str) -> tuple[bool, list[str]]:
        """
        Validate migration preserves security rules.

        Returns:
            (is_valid, list of issues found)
        """
        issues: list[str] = []

        # Required removals
        if "extends WebSecurityConfigurerAdapter" in migrated:
            issues.append("Still extends WebSecurityConfigurerAdapter")

        if "antMatchers" in migrated:
            issues.append("antMatchers not converted to requestMatchers")

        if "authorizeRequests()" in migrated and "authorizeHttpRequests" not in migrated:
            issues.append("authorizeRequests not converted to authorizeHttpRequests")

        if "EnableGlobalMethodSecurity" in migrated:
            issues.append("EnableGlobalMethodSecurity not converted to EnableMethodSecurity")

        # Required additions
        if "@Bean" not in migrated or "SecurityFilterChain" not in migrated:
            issues.append("Missing @Bean SecurityFilterChain")

        if "return http.build()" not in migrated:
            issues.append("Missing return http.build()")

        # Lambda DSL check
        and_count = migrated.count(".and()")
        if and_count > 0:
            issues.append(f"Still using .and() chaining ({and_count} occurrences)")

        # Preserve URL patterns from original
        original_urls = set(re.findall(r'"(/[^"]*)"', original))
        migrated_urls = set(re.findall(r'"(/[^"]*)"', migrated))
        lost_urls = original_urls - migrated_urls
        if lost_urls:
            issues.append(f"URL patterns lost: {lost_urls}")

        # Preserve role checks
        original_roles = set(re.findall(r'hasRole\("([^"]+)"\)', original))
        migrated_roles = set(re.findall(r'hasRole\("([^"]+)"\)', migrated))
        lost_roles = original_roles - migrated_roles
        if lost_roles:
            issues.append(f"Role checks lost: {lost_roles}")

        # Check key security features are preserved
        for feature in ["formLogin", "logout", "csrf", "cors", "httpBasic"]:
            if feature in original and feature not in migrated:
                issues.append(f"Security feature lost: {feature}")

        return len(issues) == 0, issues
