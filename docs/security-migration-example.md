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
