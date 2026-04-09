# CHECK - Code Review and Quality Assurance

## Overview
The CHECK skill provides a systematic approach to reviewing code for correctness, security, maintainability, and performance. It ensures thorough, constructive reviews that improve code quality.

## Workflow

### 1. Review Preparation
- Understand the context: what is the purpose of these changes?
- Review the ticket, spec, or issue that prompted the changes
- Understand the scope: what files and components are affected?
- Check that tests exist and are passing
- Review the commit history for clarity and logical grouping

### 2. Correctness Review
- Verify the code does what it claims to do (match against requirements)
- Check for logical errors: off-by-one, null handling, boundary conditions
- Verify error handling: are errors caught and handled appropriately?
- Check state management: no race conditions, no lost updates, proper cleanup
- Verify data transformations: inputs, outputs, and intermediate values are correct
- Look for edge cases: empty inputs, large inputs, special characters, timeouts

### 3. Security Review
- Check for injection vulnerabilities: SQL, command, XSS
- Verify authentication and authorization checks are in place
- Ensure sensitive data is not logged or exposed in error messages
- Check for proper input validation and sanitization
- Verify secrets are not hardcoded (API keys, passwords, tokens)
- Review access controls: can unauthorized users access restricted operations?

### 4. Code Quality Review
- Check naming: do names clearly communicate purpose?
- Evaluate complexity: can complex logic be simplified or extracted?
- Check for DRY violations: is the same logic duplicated?
- Verify consistency with project conventions and style
- Review error messages: are they helpful and actionable?
- Check for appropriate use of design patterns (not over-engineered)

### 5. Performance Review
- Identify obvious performance bottlenecks: N+1 queries, unbounded loops
- Check for unnecessary computation or memory allocation
- Verify appropriate data structures are used
- Check for proper use of caching where applicable
- Review database queries: proper indexing, no full table scans on large tables
- Consider scalability: will this work at 10x the current load?

### 6. Testing Review
- Verify tests cover the happy path and edge cases
- Check test quality: tests should be clear, deterministic, and maintainable
- Verify tests actually test the behavior they claim to test
- Check for proper mocking: external dependencies should be mocked appropriately
- Ensure tests are not brittle (dependent on implementation details)

## Best Practices
- Be constructive: suggest improvements, do not just point out problems
- Praise good code; positive feedback is as important as critical feedback
- Prioritize feedback: block, suggest, nitpick
- Explain why, not just what: "This could cause X because Y" is more helpful than "Fix this"
- Suggest specific alternatives when possible
- Do not block for style preferences that are consistent with project norms
- Focus on the code, not the author

## Review Checklist
- [ ] Code meets the stated requirements
- [ ] Error handling is comprehensive
- [ ] No security vulnerabilities identified
- [ ] Code is readable and well-named
- [ ] No obvious performance issues
- [ ] Tests are adequate and well-written
- [ ] Documentation updated if needed
- [ ] Consistent with project conventions
