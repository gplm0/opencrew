# DESIGN - System Architecture and UI/UX Design Planning

## Overview
The DESIGN skill provides a structured workflow for creating system architectures and user interface designs. It ensures designs are well-reasoned, user-centered, and technically feasible.

## Workflow

### 1. Requirements Analysis
- Gather functional requirements: what must the system do?
- Gather non-functional requirements: performance, scalability, security, availability
- Identify user personas and their primary workflows
- Define success metrics and how they will be measured
- Document constraints: budget, timeline, technology stack, team skills

### 2. System Architecture Design
- Identify the major components/services and their responsibilities
- Define interfaces between components (APIs, events, data flow)
- Choose architectural patterns appropriate for the problem (MVC, microservices, event-driven, layered)
- Design data models: entities, relationships, storage strategy
- Plan for scalability: horizontal vs. vertical, stateless vs. stateful components
- Address cross-cutting concerns: authentication, logging, error handling, caching

### 3. Data Flow and State Design
- Map critical data flows from user action to persistence
- Identify where state lives and how it moves between components
- Design for eventual consistency where appropriate
- Plan data partitioning and access patterns
- Consider data migration strategy if replacing an existing system

### 4. UI/UX Design
- Create user journey maps for each primary persona
- Design information architecture: navigation structure, content hierarchy
- Sketch wireframes for key screens (low-fidelity first)
- Define interaction patterns: how users complete primary tasks
- Plan responsive behavior across device sizes
- Ensure accessibility: WCAG guidelines, keyboard navigation, screen reader support

### 5. Technology Selection
- Evaluate technology options against requirements and constraints
- Consider team familiarity, community support, and long-term maintainability
- Assess integration requirements with existing systems
- Plan for observability: metrics, logging, tracing from day one
- Document technology decisions and their rationale (architecture decision records)

### 6. Risk Assessment and Validation
- Identify technical risks and propose mitigation strategies
- Create a proof-of-concept for the highest-risk components
- Review the design against requirements: does everything have coverage?
- Conduct a design review with stakeholders; incorporate feedback
- Define what can be validated in an MVP vs. deferred to later phases

## Best Practices
- Favor simplicity: the simplest design that meets requirements is usually the best
- Design for failure: every component should have error handling and recovery paths
- Keep components loosely coupled and highly cohesive
- Document assumptions and decisions; future maintainers need context
- Plan for observability from the start; retrofitting monitoring is expensive
- Design APIs to be intuitive: a good API is its own documentation
- Consider the developer experience: how easy is it to build on this architecture?

## Deliverables
- Architecture diagram (component view and deployment view)
- Data model with entity relationships
- API contracts or interface definitions
- UI wireframes for key user flows
- Technology decision log with rationale
- Risk register with mitigation strategies
