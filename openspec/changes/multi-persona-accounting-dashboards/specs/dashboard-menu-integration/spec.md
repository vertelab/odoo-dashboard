## ADDED Requirements

### Requirement: Dashboard menu mode
The system SHALL support a `menu_mode` field on `dashboard.dashboard` with values `submenu` (default) and `replace`, controlling whether the dashboard appears as a child menu or replaces the parent menu's action.

#### Scenario: Dashboard as submenu
- **WHEN** a dashboard is created with `menu_mode = "submenu"` and `parent_menu_id` pointing to "Accounting"
- **THEN** the dashboard menu item appears as a child under "Accounting", leaving the original Accounting menu action unchanged

#### Scenario: Dashboard replaces main menu
- **WHEN** a dashboard is created with `menu_mode = "replace"` and `replaces_menu_id` pointing to the "Accounting" menu
- **THEN** the Accounting menu's `action` field is set to the dashboard's `ir.actions.client`, and the original action is stored for restoration

#### Scenario: Restore original menu action on delete
- **WHEN** a dashboard with `menu_mode = "replace"` is deleted
- **THEN** the replaced menu's original action is restored

#### Scenario: Restore original menu action when mode changed to submenu
- **WHEN** a dashboard's `menu_mode` is changed from `replace` to `submenu`
- **THEN** the replaced menu's original action is restored, and a child menu item is created instead

### Requirement: Original menu action preservation
The system SHALL store the original `ir.actions.client` or `ir.actions.act_window` reference of a replaced menu so it can be restored.

#### Scenario: Store and restore
- **WHEN** a dashboard replaces "Accounting" menu which originally pointed to `action_account_journal_form`
- **THEN** the original action reference (e.g., `ir.actions.act_window,123`) is stored on the dashboard record and restored when the replacement is removed

### Requirement: Menu mode in dashboard-as-code YAML
The system SHALL support `menu_mode` and `replaces_menu` in the dashboard YAML definition.

#### Scenario: YAML dashboard replacing a menu
- **WHEN** a YAML dashboard defines `menu_mode: replace` and `replaces_menu: accounting.menu_finance`
- **THEN** loading the YAML replaces the Accounting menu's action with this dashboard
