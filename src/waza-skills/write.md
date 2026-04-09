# WRITE - Clear Technical Writing and Documentation

## Overview
The WRITE skill provides a systematic approach to producing clear, accurate, and well-structured technical content. Whether writing documentation, specifications, or explanations, this workflow ensures consistency and quality.

## Workflow

### 1. Audience Analysis
- Identify the target audience and their technical proficiency level
- Determine what the reader already knows vs. what needs to be explained
- Define the reader's goal: what should they be able to do after reading?
- Choose appropriate tone: formal specification, tutorial, reference, or overview
- Consider accessibility: avoid jargon without definition, explain acronyms

### 2. Content Planning
- Define the document's purpose in one sentence
- Create an outline with logical section hierarchy
- Determine the scope: what to include and what to exclude
- Identify supporting materials needed (diagrams, code examples, tables)
- Decide on the structure: getting-started, reference, tutorial, or conceptual

### 3. Drafting
- Start with an introduction that sets context and expectations
- Follow the outline strictly; restructure only if it improves clarity
- Use the inverted pyramid: most important information first
- Write in active voice; prefer "the system validates input" over "input is validated by the system"
- Keep paragraphs focused: one main idea per paragraph (3-5 sentences)
- Include code examples that are minimal, complete, and runnable

### 4. Technical Accuracy Review
- Verify all code examples actually work as described
- Check that all technical claims are accurate and current
- Ensure version numbers, API names, and configuration values are correct
- Cross-reference any external links or documentation references
- Validate that commands and file paths are accurate for the target platform

### 5. Clarity and Style Review
- Eliminate ambiguity: replace vague terms ("some", "usually") with specifics
- Ensure consistent terminology: do not alternate between synonyms for the same concept
- Check heading hierarchy is logical and consistent (H2 > H3 > H4)
- Verify formatting is consistent: code in backticks, filenames in backticks, emphasis for key terms
- Remove redundancy: if two sentences say the same thing, keep the clearer one

### 6. Final Polish
- Check spelling, grammar, and punctuation
- Ensure all cross-references and anchors work correctly
- Verify the document has a clear beginning and ending (no abrupt stops)
- Add a summary or next-steps section if the document is long
- Run a final read-through focusing on flow and transitions between sections

## Best Practices
- Write for scanning: use headings, lists, code blocks, and tables to break up text
- Show, don't just tell: prefer examples over abstract descriptions
- Keep documentation close to the code it describes (minimize drift)
- Update documentation when code changes; treat docs as part of the codebase
- Use consistent formatting: establish a style guide and follow it
- Write error messages and troubleshooting sections for known failure modes

## Common Document Types
- **README**: Project overview, quick start, contribution guide
- **API Documentation**: Endpoints, parameters, examples, error responses
- **Architecture Decision Records (ADR)**: Context, decision, consequences
- **Tutorial**: Step-by-step guide with expected outcomes at each step
- **Reference**: Comprehensive, structured listing of options, parameters, types
