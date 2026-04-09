# READ - Content Analysis and Extraction

## Overview
The READ skill provides a systematic approach to analyzing, understanding, and extracting value from content of any type: code, documentation, specifications, research papers, and technical articles.

## Workflow

### 1. Content Assessment
- Identify the content type: code, documentation, article, specification, paper
- Estimate length and complexity; allocate appropriate time
- Determine the purpose: learn, reference, review, extract specific information
- Identify the author's apparent intent: teach, inform, persuade, specify
- Check the date and version; assess currency and relevance

### 2. Structural Analysis
- Scan the structure: headings, sections, table of contents, file organization
- Identify the main argument or thesis (for prose) or architecture (for code)
- Note key sections and their relationships
- Identify prerequisites or context needed to fully understand the content
- Look for summaries, conclusions, or TL;DR sections first

### 3. Deep Reading
- Read actively: question, annotate, and summarize as you go
- For code: trace execution flow, identify data structures, note side effects
- For documentation: extract key concepts, APIs, configurations, examples
- For articles: identify main claims, evidence, and conclusions
- Mark sections that are unclear for re-reading or further research
- Note patterns, conventions, and design decisions

### 4. Information Extraction
- Extract actionable information: commands, configurations, API usage patterns
- Capture key insights and non-obvious observations
- Note any assumptions the content makes about the reader
- Extract code patterns and idioms used
- Document any questions or contradictions that arise

### 5. Comprehension Verification
- Summarize the content in your own words (can you explain it simply?)
- Identify any gaps: what is assumed but not explained?
- Check for internal consistency: do claims and examples align?
- Verify technical accuracy against authoritative sources where possible
- Test code examples if applicable

### 6. Knowledge Integration
- Connect the content to your existing knowledge
- Identify how this content changes or confirms your understanding
- Note practical applications: what can you do with this information?
- File the knowledge appropriately: reference material vs. core concept
- Create a brief summary for future reference

## Best Practices
- Read the README, overview, or abstract before diving into details
- For code, start with the public interface before examining implementation
- Look for tests: they reveal intended behavior and edge cases
- Pay attention to naming conventions; they reveal design intent
- When reading large codebases, follow one execution path at a time
- Use search strategically: find definitions, usages, and references
- Do not try to understand everything; focus on what is relevant to your goal

## Reading Strategies by Content Type
- **Code**: Interface first, then implementation. Follow execution paths. Read tests.
- **Documentation**: Overview first, then deep-dive into relevant sections. Try examples.
- **Technical Article**: Abstract and conclusions first, then methodology/details.
- **Specification**: Structure and definitions first, then rules and constraints.
- **Research Paper**: Abstract, introduction, conclusion, then figures, then methods.

## Output Template
When summarizing analyzed content:
1. Content type and source
2. Main purpose and thesis
3. Key findings or insights (bullet list)
4. Important details extracted (code, configs, facts)
5. Questions or ambiguities identified
6. Practical implications or next steps
