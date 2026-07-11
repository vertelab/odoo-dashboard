## ADDED Requirements

### Requirement: Two user groups
The system SHALL define two access groups: group_dashboard_user (inherits base.group_user) and group_dashboard_manager (inherits group_dashboard_user).

#### Scenario: User permission
- **WHEN** a user is in group_dashboard_user but NOT group_dashboard_manager
- **THEN** the user can view dashboards assigned to them but cannot edit dashboard configuration

#### Scenario: Manager permission
- **WHEN** user is in group_dashboard_manager
- **THEN** user can create, edit, and delete dashboards, metrics, and charts

### Requirement: Dashboard-level access control
The system SHALL support dashboard access via user_ids, group_ids, and access_by (access_group/user) with corresponding ir.rule.

#### Scenario: Dashboard restricted to specific users
- **WHEN** a dashboard has user_ids set to [User A, User B]
- **THEN** only User A and User B can see the dashboard in their menu

#### Scenario: Dashboard open to all
- **WHEN** a dashboard has user_ids = False (empty)
- **THEN** all users with group_dashboard_user can see it

### Requirement: Per-chart group access via ir.rule
The system SHALL enforce chart_group_ids via ir.rule, not just a runtime filter.

#### Scenario: Chart restricted to group
- **WHEN** chart A has chart_group_ids = ["Sales Managers"] and chart B has no group restriction
- **THEN** only Sales Managers can see chart A; all dashboard users can see chart B

#### Scenario: Chart access via direct API
- **WHEN** a non-Sales-Manager user queries dashboard.chart directly via RPC
- **THEN** the ir.rule filters out charts with chart_group_ids they don't belong to

### Requirement: Server-side write/create/unlink protection
The system SHALL restrict write, create, and unlink operations on dashboard records to group_dashboard_manager via model access rights.

#### Scenario: User cannot modify dashboard
- **WHEN** a group_dashboard_user (not manager) attempts to write to a dashboard record
- **THEN** the operation is denied by model access (perm_write=0 for group_dashboard_user)

#### Scenario: Manager can modify
- **WHEN** a group_dashboard_manager writes to a dashboard record
- **THEN** the operation succeeds

### Requirement: Row-level data security per source type
The system SHALL handle row-level security differently based on source_type: model uses ORM automatically, sql uses security bridge (authorized_ids), service relies on adapter declaration.

#### Scenario: Model source with ir.rule
- **WHEN** a model-source metric on sale.order is evaluated for a user with team-based ir.rule
- **THEN** _read_group() automatically applies the team filter and returns only the user's team data

#### Scenario: SQL source with security bridge
- **WHEN** a sql-source metric runs a custom query
- **THEN** the security bridge first calls Model.search() to get authorized IDs, then adds `WHERE id = ANY($ids)` to the SQL

#### Scenario: Service source declaration
- **WHEN** a service source declares security.respects_ir_rule=false in get_schema()
- **THEN** dashboard_vrtl warns that the source does not respect user access restrictions, but still allows use
