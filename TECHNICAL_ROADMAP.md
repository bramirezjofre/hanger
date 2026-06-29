# Technical Roadmap

This roadmap converts the current product notes in `ROADMAP.md` into implementable engineering work for `hanger_app`. It focuses on the next backend, security, operations, and documentation milestones.

## 1. Controlled User Onboarding

Goal: only register users who pass a selection process.

Implementation scope:

<<<<<<< HEAD
- [x] Add an application workflow with states: `submitted`, `screening`, `interview`, `accepted`, `rejected`, and `invited`.
- [x] Store application answers, reviewer notes, decision timestamps, and reviewer user IDs.
- [x] Replace open registration with invite-only registration tied to accepted applications.
- [~] Add admin routes and CLI commands to review, accept, reject, and invite applicants.
  CLI commands are implemented; dedicated application-review admin routes remain pending.
- [~] Add audit events for every application state change.
  CLI accept, reject, and invite actions are audited; full service-level transition auditing remains pending.
=======
- Add an application workflow with states: `submitted`, `screening`, `interview`, `accepted`, `rejected`, and `invited`.
- Store application answers, reviewer notes, decision timestamps, and reviewer user IDs.
- Replace open registration with invite-only registration tied to accepted applications.
- Add admin routes and CLI commands to review, accept, reject, and invite applicants.
- Add audit events for every application state change.
>>>>>>> 699c59b (Resstructure MARDOWNS files)

Acceptance criteria:

- [x] A non-invited user cannot create an account.
- [x] Accepted applicants receive a single-use invitation.
- [~] Tests cover duplicate applications, rejected applications, expired invites, and admin-only decisions.
  Rejected applications, expired invites, single-use tokens, and route protections are covered; duplicate application and full admin-only application decision coverage remain pending.

## 2. Per-Installation Requirements

Goal: support different eligibility rules and operating limits for each deployed server.

Implementation scope:

<<<<<<< HEAD
- [x] Introduce an `installation_settings` table for onboarding rules, eligibility criteria, limits, and branding.
- [x] Move server-specific values out of source code into environment variables or database-backed settings.
- [x] Validate required production settings during application startup.
- [x] Add an admin UI or CLI for reading and updating safe settings.
  CLI support is implemented with `settings-list`, `settings-get`, and `settings-set`.
- [~] Document required configuration in `README.md` and deployment examples.
  `README.md` and contributor commands are updated; richer deployment examples remain pending.
=======
- Introduce an `installation_settings` table for onboarding rules, eligibility criteria, limits, and branding.
- Move server-specific values out of source code into environment variables or database-backed settings.
- Validate required production settings during application startup.
- Add an admin UI or CLI for reading and updating safe settings.
- Document required configuration in `README.md` and deployment examples.
>>>>>>> 699c59b (Resstructure MARDOWNS files)

Acceptance criteria:

- [x] Each deployment can define its own eligibility rules without code changes.
- [x] Missing production configuration fails fast with a clear error.
- [x] Tests verify default settings, overrides, and invalid configuration.

## 3. Interview and Research Pipeline

Goal: manage interviews with possible future users and convert research into actionable product signals.
<<<<<<< HEAD

Implementation scope:

- [ ] Add applicant interview scheduling fields: contact method, preferred times, assigned interviewer, and status.
- [ ] Add interview notes with structured categories: motivation, fit, risks, and follow-up actions.
- [ ] Add privacy controls so only admins or assigned interviewers can read interview notes.
- [ ] Add aggregate exports for research metrics without exposing sensitive notes.
=======

Implementation scope:

- Add applicant interview scheduling fields: contact method, preferred times, assigned interviewer, and status.
- Add interview notes with structured categories: motivation, fit, risks, and follow-up actions.
- Add privacy controls so only admins or assigned interviewers can read interview notes.
- Add aggregate exports for research metrics without exposing sensitive notes.
>>>>>>> 699c59b (Resstructure MARDOWNS files)

Acceptance criteria:

- [ ] Interview notes are access-controlled and audited.
- [ ] Admins can list applicants by interview status.
- [ ] Research exports exclude private free-text notes by default.

## 4. Funding and Operations Readiness

Goal: prepare the project for external funding, sponsorship, or structured collaboration.
<<<<<<< HEAD

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
=======

Implementation scope:

- Add operational metrics: registered users, active users, applications by status, invitation conversion, and message/job health.
- Add health dashboards or CLI reports using the existing `/health/live` and `/health/ready` foundations.
- Improve logging around authentication, onboarding, background jobs, and upload access decisions.
- Add data retention policies for applications, interview notes, and recovery tokens.
- Add backup and restore documentation for SQLite deployments.

Acceptance criteria:

- Maintainers can generate a funding-ready usage report without direct database inspection.
- Sensitive user data is excluded from public or sponsor-facing exports.
- Backup and restore steps are documented and tested against a local database.
>>>>>>> 699c59b (Resstructure MARDOWNS files)

## Cross-Cutting Engineering Priorities

- Security: preserve invite token single-use semantics, role-based access control, audit logs, and upload authorization.
- Testing: keep coverage above the CI threshold and add route/service tests for every onboarding decision path.
- Migrations: add schema changes only through numbered files in `src/hanger_app/migrations/`; never rewrite applied migrations.
- Documentation: update `AGENTS.md`, `README.md`, and deployment notes whenever commands, configuration, or workflows change.
- Observability: prefer structured logs and explicit health checks over silent failures.

## Suggested Implementation Order

<<<<<<< HEAD
1. [x] Add application and invitation schema.
2. [x] Implement repository and service layer for application decisions.
3. [~] Add admin CLI commands and protected admin routes.
4. [x] Disable open registration when invite-only mode is enabled.
5. [x] Add installation settings and production validation.
6. [ ] Add interview notes and access controls.
7. [ ] Add reporting commands and sanitized exports.
8. [~] Document deployment, backup, restore, and operational workflows.
=======
1. Add application and invitation schema.
2. Implement repository and service layer for application decisions.
3. Add admin CLI commands and protected admin routes.
4. Disable open registration when invite-only mode is enabled.
5. Add installation settings and production validation.
6. Add interview notes and access controls.
7. Add reporting commands and sanitized exports.
8. Document deployment, backup, restore, and operational workflows.
>>>>>>> 699c59b (Resstructure MARDOWNS files)

## Spanish Summary

Esta hoja de ruta traduce las ideas de `ROADMAP.md` en trabajo técnico concreto para `hanger_app`.

### 1. Registro controlado de usuarios

Solo deben registrarse usuarios que pasen un proceso de selección. Para lograrlo, el proyecto necesita solicitudes de ingreso, estados de revisión, invitaciones de un solo uso, rutas administrativas, comandos CLI y auditoría de cada decisión.

### 2. Reglas por instalación

<<<<<<< HEAD
Cada servidor debe poder definir sus propios criterios de elegibilidad, límites operativos y configuración sin modificar código. Esto requiere una tabla de configuración, validaciones al iniciar la aplicación y documentación clara para despliegues.
=======
- Un usuario sin invitar no puede registrarse.
- Los usuarios aprovados reciben una sola invitación.
- Los test cubren detalles comunes de seguridad.

## Fase 2: Requisitos de Pre-Instalación
>>>>>>> 9e301ca (Fix MARKDOWNS file Structure)

<<<<<<< HEAD
### 3. Entrevistas e investigación

El sistema debe ayudar a coordinar entrevistas con posibles usuarios, registrar notas estructuradas y proteger la información sensible. Los reportes deben entregar métricas agregadas sin exponer notas privadas.

### 4. Preparación operacional y financiamiento

<<<<<<< HEAD
El proyecto debe poder mostrar métricas de uso, salud del sistema y evidencia operacional para colaboración externa o financiamiento. También necesita mejores logs, políticas de retención y documentación de respaldo/restauración.
=======
- .
- .
- .
>>>>>>> 9e301ca (Fix MARKDOWNS file Structure)
=======
Cada servidor debe poder definir sus propios criterios de elegibilidad, límites operativos y configuración sin modificar código. Esto requiere una tabla de configuración, validaciones al iniciar la aplicación y documentación clara para despliegues.

### 3. Entrevistas e investigación

El sistema debe ayudar a coordinar entrevistas con posibles usuarios, registrar notas estructuradas y proteger la información sensible. Los reportes deben entregar métricas agregadas sin exponer notas privadas.

### 4. Preparación operacional y financiamiento

El proyecto debe poder mostrar métricas de uso, salud del sistema y evidencia operacional para colaboración externa o financiamiento. También necesita mejores logs, políticas de retención y documentación de respaldo/restauración.
>>>>>>> 699c59b (Resstructure MARDOWNS files)
