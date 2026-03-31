<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 → 1.0.0 (MAJOR - initial ratification)

  Modified principles: N/A (initial version)

  Added sections:
    - Principle I: Code Quality & Maintainability
    - Principle II: Testing Standards
    - Principle III: User Experience Consistency
    - Principle IV: Performance Requirements
    - Section: Architecture Constraints (frontend/backend separation)
    - Section: Development Workflow
    - Governance rules

  Removed sections: N/A (initial version)

  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no update needed (Constitution Check
      section is dynamic; plan command reads constitution at runtime)
    - .specify/templates/spec-template.md ✅ no update needed (spec template is
      generic; constitution principles are enforced at review time)
    - .specify/templates/tasks-template.md ✅ no update needed (task phases and
      parallel markers already accommodate testing and performance tasks)

  Follow-up TODOs: None
-->

# TuneMuse Constitution

## Core Principles

### I. Code Quality & Maintainability

All production code MUST adhere to the following non-negotiable standards:

- **Readability first**: Code MUST be written for humans to read and maintain.
  Variable names, function signatures, and module structure MUST convey intent
  without requiring external documentation.
- **Detailed comments**: Every function and class MUST have documentation
  comments explaining purpose, parameters, and return values. Complex logic
  MUST include inline comments explaining the reasoning, written in plain
  language accessible to junior developers.
- **Consistent formatting**: All code MUST pass the project's configured linter
  and formatter before merge. No exceptions.
- **Library-first**: Prefer mature, actively maintained open-source libraries
  over custom implementations for common functionality. Custom code MUST be
  justified when an established solution exists.
- **No dead code**: Unused imports, variables, functions, and commented-out
  code blocks MUST be removed before merge.
- **Type safety**: Both frontend and backend code MUST use static typing
  (TypeScript for frontend, typed language or type annotations for backend).

### II. Testing Standards

Testing is mandatory for all features and bug fixes:

- **Unit tests required**: Every service, utility, and business logic module
  MUST have corresponding unit tests covering normal paths, edge cases, and
  error conditions.
- **Integration tests for boundaries**: All API endpoints, database operations,
  and cross-service communication MUST have integration tests that run against
  real dependencies (no mocks for infrastructure boundaries).
- **Contract tests for APIs**: Every frontend-backend API contract MUST have
  contract tests verifying request/response schemas. Breaking a contract test
  MUST block the merge.
- **Coverage threshold**: New code MUST maintain or improve the project's test
  coverage. No PR may reduce overall coverage below the configured minimum.
- **Test independence**: Each test MUST be independently runnable. Tests MUST
  NOT depend on execution order or shared mutable state.

### III. User Experience Consistency

All user-facing interfaces MUST deliver a cohesive, predictable experience:

- **Design system compliance**: All UI components MUST use the project's
  shared design system (tokens, components, patterns). Ad-hoc styling is
  prohibited in production code.
- **Responsive by default**: Every page and component MUST render correctly
  on mobile (≥320px), tablet (≥768px), and desktop (≥1024px) viewports.
- **Accessibility baseline**: All interfaces MUST meet WCAG 2.1 Level AA.
  This includes keyboard navigation, screen reader compatibility, sufficient
  color contrast, and proper ARIA attributes.
- **Loading states**: Every asynchronous operation MUST display appropriate
  loading feedback. Users MUST never face a blank or frozen screen.
- **Error communication**: All errors MUST be surfaced to users with clear,
  actionable messages. Technical details (stack traces, error codes) MUST
  NOT be shown to end users.
- **Consistent interaction patterns**: Navigation, form behavior, modals,
  and notifications MUST follow the same patterns across all pages.

### IV. Performance Requirements

Performance is a feature, not an afterthought:

- **Page load budget**: Initial page load (Largest Contentful Paint) MUST
  be under 2.5 seconds on a 4G connection. Time to Interactive MUST be
  under 3.5 seconds.
- **API response budget**: All API endpoints MUST respond within 200ms at
  p95 under normal load. Endpoints exceeding 500ms at p95 MUST be flagged
  for optimization.
- **Bundle size discipline**: Frontend JavaScript bundle size MUST NOT
  exceed the configured budget. Every new dependency MUST be evaluated for
  its size impact. Tree-shaking and code-splitting MUST be used.
- **Database query limits**: No single user request SHOULD trigger more
  than 5 database queries (N+1 queries are prohibited). All queries MUST
  use appropriate indexes.
- **Benchmark-driven optimization**: Performance changes MUST be backed by
  benchmark data showing before/after metrics. Optimizations without
  measurable improvement MUST be reverted.
- **Monitoring**: Key performance indicators (response time, error rate,
  throughput) MUST be instrumented and observable in production.

## Architecture Constraints

This project follows a **frontend/backend separation** architecture:

- **Decoupled deployments**: Frontend and backend MUST be independently
  deployable. Neither side may assume co-location or shared process memory.
- **API-first communication**: All frontend-backend interaction MUST go
  through versioned REST or GraphQL APIs. No direct database access from
  the frontend.
- **Shared contracts**: API schemas (OpenAPI, GraphQL SDL, or equivalent)
  MUST be the single source of truth for the interface between frontend
  and backend. Both sides MUST validate against these contracts.
- **Independent tech stacks**: Frontend and backend MAY use different
  languages, frameworks, and build tools. Shared code MUST be limited to
  API type definitions and constants.
- **CORS and security**: Backend MUST implement proper CORS policies.
  Authentication tokens MUST be handled securely (HttpOnly cookies or
  secure token storage, never localStorage for sensitive tokens).

## Development Workflow

All contributors MUST follow this workflow:

- **Branch-per-feature**: Every feature, bug fix, or improvement MUST be
  developed on a dedicated branch. Direct commits to the main branch are
  prohibited.
- **PR review required**: All code MUST be reviewed by at least one other
  developer before merge. Self-merges are prohibited for production code.
- **CI must pass**: All automated checks (lint, type-check, tests, build)
  MUST pass before a PR can be merged. No bypassing CI failures.
- **Atomic commits**: Each commit SHOULD represent a single logical change
  with a clear, descriptive message following conventional commit format.
- **Documentation updates**: Any change that affects public APIs, user
  workflows, or deployment procedures MUST include corresponding
  documentation updates in the same PR.

## Governance

This constitution is the authoritative source of engineering standards for
the TuneMuse project. It supersedes informal conventions, verbal agreements,
and ad-hoc practices.

- **Amendment process**: Any change to this constitution MUST be proposed
  as a PR, reviewed by the team, and approved before merge. The version
  number MUST be incremented per semantic versioning rules.
- **Versioning policy**: MAJOR for principle removals or incompatible
  redefinitions; MINOR for new principles or material expansions; PATCH
  for clarifications, wording fixes, or non-semantic refinements.
- **Compliance review**: All PRs and code reviews MUST verify compliance
  with these principles. Violations MUST be resolved before merge unless
  explicitly justified in the Complexity Tracking section of the
  implementation plan.
- **Conflict resolution**: When a principle conflicts with a practical
  constraint, the deviation MUST be documented with rationale and an
  approved exception in the relevant plan or spec document.

**Version**: 1.0.0 | **Ratified**: 2026-03-29 | **Last Amended**: 2026-03-29
