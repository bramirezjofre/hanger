# [EN] Technical Roadmap

This roadmap converts the current product notes into implementable engineering work for `hanger_app`.

## Phase 1: Controlled User Onboarding

Goal: only register users who pass a selection process.

- Add an application workflow with states: `submitted`, `screening`, `interview`, `accepted`, `rejected`, and `invited`.
- Store application answers, reviewer notes, decision timestamps, and reviewer user IDs.
- Replace open registration with invite-only registration tied to an accepted application.
- Add admin routes and CLI commands to review, accept, reject, and invite applicants.
- Add audit events for every application state change.

Acceptance criteria:

- A non-invited user cannot create an account.
- Accepted applicants receive a single-use invitation.
- Tests cover duplicate applications, rejected applications, expired invites, and admin-only decisions.

## Phase 2: Per-Installation Requirements

Goal: support different rules for each deployed server.

- Introduce an `installation_settings` table for configurable onboarding, eligibility, limits, and branding.
- Move server-specific values out of code into environment variables and database-backed settings.
- Add validation for required production settings during app startup.
- Add admin UI/CLI for reading and updating safe settings.
- Document required configuration in `README.md` and deployment examples.

Acceptance criteria:

- Each deployment can define its own eligibility rules without code changes.
- Missing production configuration fails fast with a clear error.
- Tests verify default settings, overrides, and invalid configuration.

## Phase 3: Interview and Research Pipeline

Goal: manage interviews with possible future users.

- Add applicant interview scheduling fields: contact method, preferred times, assigned interviewer, and status.
- Add interview notes with structured categories: motivation, fit, risks, and follow-up actions.
- Add privacy controls so only admins or assigned interviewers can read interview notes.
- Add export/reporting commands for aggregate research metrics without exposing sensitive notes.

Acceptance criteria:

- Interview notes are access-controlled and audited.
- Admins can list applicants by interview status.
- Research exports exclude private free-text notes by default.

## Phase 4: Funding and Operations Readiness

Goal: prepare the project for external funding or sponsorship.

- Add operational metrics: registered users, active users, applications by status, invitation conversion, and message/job health.
- Add health dashboards or CLI reports using existing `/health/live` and `/health/ready` foundations.
- Improve logging around authentication, onboarding, background jobs, and upload access decisions.
- Add data retention policies for applications, interview notes, and recovery tokens.
- Add backup and restore documentation for SQLite deployments.

Acceptance criteria:

- Maintainers can generate a funding-ready usage report without direct database inspection.
- Sensitive user data is excluded from public or sponsor-facing exports.
- Backup/restore steps are documented and tested against a local database.

## Cross-Cutting Engineering Priorities

- Security: preserve invite token single-use semantics, role-based access control, audit logs, and upload authorization.
- Testing: keep coverage above the CI threshold and add route/service tests for every onboarding decision path.
- Migrations: add new schema changes only through numbered files in `src/hanger_app/migrations/`; never rewrite applied migrations.
- Documentation: update `AGENTS.md`, `README.md`, and deployment notes whenever commands, configuration, or workflows change.
- Observability: prefer structured logs and explicit health checks over silent failures.

## Suggested Implementation Order

1. Add application and invitation schema.
2. Implement repository/service layer for application decisions.
3. Add admin CLI and protected admin routes.
4. Disable open registration when invite-only mode is enabled.
5. Add installation settings and production validation.
6. Add interview notes and access controls.
7. Add reporting commands and sanitized exports.
8. Document deployment, backup, restore, and operational workflows.
<hr/>
# [ES] Proximos Pasos

## Fase 1: Registro Controlado De usuarios

Objetivos: Solo registrar usuarios que pasaron proceso de selección.

- .
- .
- .
- .
- .

Verificación:

- .
- .
- .
## Fase 2: 

Objetivos: .

- .
- .
- .
- .
- .

Verificación:

- .
- .
- .

## Fase 3: 

Objetivos: .

- .
- .
- .
- .

Verificación:

- .
- .
- .

## Fase 4: 

Objetivos: .

- .
- .
- .
- .
- .

Varificación:

- .
- .
- .
  
## Prioridad De Conceptos Clave

-
-
-
-
-

## Orden De Implementación Sugerido

1. .
2. .
3. .
4. .
5. .
6. .
7. .
8. .
<hr/>
# [FR] 

## 1

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
## 2

: .

- .
- .
- .
- .
- .

:

- .
- .
- .

## 3

: .

- .
- .
- .
- .

:

- .
- .
- .

## 4

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
  
## 

-
-
-
-
-

## 

1. .
2. .
3. .
4. .
5. 
6. .
7. .
8. .
<hr/>
# [PT] 

## Fase 1:

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
## Fase 2: 

: .

- .
- .
- .
- .
- .

:

- .
- .
- .

## Fase 3: 

: .

- .
- .
- .
- .

:

- .
- .
- .

## Fase 4: 

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
  
##

-
-
-
-
-

##

1. .
2. .
3. .
4. .
5. 
6. .
7. .
8. .
<hr/>
# [DE] 

## Phase 1: 

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
## Phase 2: 

: .

- .
- .
- .
- .
- .

:

- .
- .
- .

## Phase 3: 

: .

- .
- .
- .
- .

:

- .
- .
- .

## Phase 4:

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
  
##

-
-
-
-
-

##

1. .
2. .
3. .
4. .
5. 
6. .
7. .
8. .
<hr/>
# [ZH] 后续步骤

## 阶段 一: 

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
## 阶段 2:

: .

- .
- .
- .
- .
- .

:

- .
- .
- .

## 阶段 3:

: .

- .
- .
- .
- .

:

- .
- .
- .

## 阶段 4:

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
  
##

-
-
-
-
-

##

1. .
2. .
3. .
4. .
5. 
6. .
7. .
8. .
<hr/>
# [RU] 

## фаза 1

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
## фаза 2

: .

- .
- .
- .
- .
- .

:

- .
- .
- .

## фаза 3

: .

- .
- .
- .
- .

:

- .
- .
- .

## фаза 4:

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
  
##

-
-
-
-
-

##

1. .
2. .
3. .
4. .
5. 
6. .
7. .
8. .
<hr/>
# [UK] 

## фаза 1

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
## фаза 2

: .

- .
- .
- .
- .
- .

:

- .
- .
- .

## фаза 3

: .

- .
- .
- .
- .

:

- .
- .
- .

## фаза 4

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
  
##

-
-
-
-
-

##

1. .
2. .
3. .
4. .
5. 
6. .
7. .
8. .
<hr/>
# [JA] 

## 段階 1

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
## 段階 2

: .

- .
- .
- .
- .
- .

:

- .
- .
- .

## 段階 3

: .

- .
- .
- .
- .

:

- .
- .
- .

## 段階 4

: .

- .
- .
- .
- .
- .

:

- .
- .
- .
  
##

-
-
-
-
-

##

1. .
2. .
3. .
4. .
5. 
6. .
7. .
8. .
<hr/>
