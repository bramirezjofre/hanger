# Technical Roadmap

This roadmap converts the current product notes in `ROADMAP.md` into implementable engineering work for `hanger_app`. It focuses on the next backend, security, operations, and documentation milestones.

## 1. Controlled User Onboarding

Goal: only register users who pass a selection process.

Implementation scope:

- [x] Add an application workflow with states: `submitted`, `screening`, `interview`, `accepted`, `rejected`, and `invited`.
- [x] Store application answers, reviewer notes, decision timestamps, and reviewer user IDs.
- [x] Replace open registration with invite-only registration tied to accepted applications.
- [~] Add admin routes and CLI commands to review, accept, reject, and invite applicants.
  CLI commands are implemented; dedicated application-review admin routes remain pending.
- [~] Add audit events for every application state change.
  CLI accept, reject, and invite actions are audited; full service-level transition auditing remains pending.

Acceptance criteria:

- [x] A non-invited user cannot create an account.
- [x] Accepted applicants receive a single-use invitation.
- [~] Tests cover duplicate applications, rejected applications, expired invites, and admin-only decisions.
  Rejected applications, expired invites, single-use tokens, and route protections are covered; duplicate application and full admin-only application decision coverage remain pending.

## 2. Per-Installation Requirements

Goal: support different eligibility rules and operating limits for each deployed server.

Implementation scope:

- [x] Introduce an `installation_settings` table for onboarding rules, eligibility criteria, limits, and branding.
- [x] Move server-specific values out of source code into environment variables or database-backed settings.
- [x] Validate required production settings during application startup.
- [x] Add an admin UI or CLI for reading and updating safe settings.
  CLI support is implemented with `settings-list`, `settings-get`, and `settings-set`.
- [~] Document required configuration in `README.md` and deployment examples.
  `README.md` and contributor commands are updated; richer deployment examples remain pending.

Acceptance criteria:

- [x] Each deployment can define its own eligibility rules without code changes.
- [x] Missing production configuration fails fast with a clear error.
- [x] Tests verify default settings, overrides, and invalid configuration.

## 3. Interview and Research Pipeline

Goal: manage interviews with possible future users and convert research into actionable product signals.

Implementation scope:

- [ ] Add applicant interview scheduling fields: contact method, preferred times, assigned interviewer, and status.
- [ ] Add interview notes with structured categories: motivation, fit, risks, and follow-up actions.
- [ ] Add privacy controls so only admins or assigned interviewers can read interview notes.
- [ ] Add aggregate exports for research metrics without exposing sensitive notes.

Acceptance criteria:

- [ ] Interview notes are access-controlled and audited.
- [ ] Admins can list applicants by interview status.
- [ ] Research exports exclude private free-text notes by default.

## 4. Funding and Operations Readiness

Goal: prepare the project for external funding, sponsorship, or structured collaboration.

Implementation scope:

- [ ] Add operational metrics: registered users, active users, applications by status, invitation conversion, and message/job health.
- [ ] Add health dashboards or CLI reports using the existing `/health/live` and `/health/ready` foundations.
- [ ] Improve logging around authentication, onboarding, background jobs, and upload access decisions.
- [ ] Add data retention policies for applications, interview notes, and recovery tokens.
- [ ] Add backup and restore documentation for SQLite deployments.

Acceptance criteria:

- [ ] Maintainers can generate a funding-ready usage report without direct database inspection.
- [ ] Sensitive user data is excluded from public or sponsor-facing exports.
- [ ] Backup and restore steps are documented and tested against a local database.

## Cross-Cutting Engineering Priorities

- Security: preserve invite token single-use semantics, role-based access control, audit logs, and upload authorization.
- Testing: keep coverage above the CI threshold and add route/service tests for every onboarding decision path.
- Migrations: add schema changes only through numbered files in `src/hanger_app/migrations/`; never rewrite applied migrations.
- Documentation: update `AGENTS.md`, `README.md`, and deployment notes whenever commands, configuration, or workflows change.
- Observability: prefer structured logs and explicit health checks over silent failures.

## Suggested Implementation Order

1. [x] Add application and invitation schema.
2. [x] Implement repository and service layer for application decisions.
3. [~] Add admin CLI commands and protected admin routes.
4. [x] Disable open registration when invite-only mode is enabled.
5. [x] Add installation settings and production validation.
6. [ ] Add interview notes and access controls.
7. [ ] Add reporting commands and sanitized exports.
8. [~] Document deployment, backup, restore, and operational workflows.

## Spanish Summary