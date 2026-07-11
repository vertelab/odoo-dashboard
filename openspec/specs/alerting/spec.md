## ADDED Requirements

### Requirement: Alert rule definition
The system SHALL provide a `dashboard.alert` model that associates a metric with a condition expression, severity level, and notification configuration.

#### Scenario: Threshold alert
- **WHEN** an alert is defined with metric="inventory.stock_level", condition="value < 10", severity="warning"
- **THEN** the system evaluates the metric periodically; when value drops below 10, a notification is triggered

#### Scenario: Delta alert
- **WHEN** an alert is defined with condition="delta < -30 and value < 50000"
- **THEN** the system compares current value with previous value; triggers when both conditions are met

### Requirement: Scheduled evaluation via ir.cron
The system SHALL evaluate cron-type alerts on a configurable schedule using ir.cron.

#### Scenario: Periodic evaluation
- **WHEN** an alert has trigger_type="cron" and schedule="0 */4 * * *" (every 4 hours)
- **THEN** the alert's condition is evaluated every 4 hours; current and previous values are compared

#### Scenario: Cooldown enforcement
- **WHEN** an alert has cooldown=3600 (1 hour) and was triggered 30 minutes ago
- **THEN** even if the condition is still met, no new notification is sent until 1 hour has passed

### Requirement: Two notification channels
The system SHALL support exactly two notification channels: notification (Odoo Discuss) and activity (Odoo Activity).

#### Scenario: Notification via Discuss
- **WHEN** an alert triggers with channel "notification"
- **THEN** a message is posted in the "Dashboard Alerts" mail.channel visible to all recipients

#### Scenario: Activity requiring action
- **WHEN** an alert triggers with channel "activity"
- **THEN** a mail.activity is created on each recipient user's "Att göra"-list with the alert details

### Requirement: Alert state machine
The system SHALL manage alert lifecycle via state transitions: ok → triggered → acknowledged → ok.

#### Scenario: Alert triggers
- **WHEN** condition evaluates to true and cooldown allows
- **THEN** state changes from "ok" to "triggered"; notifications are sent; last_triggered is updated

#### Scenario: User acknowledges
- **WHEN** user marks the activity as done or acknowledges the notification
- **THEN** state changes from "triggered" to "ok"; alert is ready to trigger again on next evaluation

#### Scenario: Auto-reset
- **WHEN** condition evaluates to false (issue resolved) while alert is in "triggered" state
- **THEN** state automatically changes to "ok" without user action

### Requirement: Alert variables
The system SHALL expose variables for condition evaluation: value (current), previous_value (last evaluation), delta (percentage change), current_hour, current_dow.

#### Scenario: Time-aware condition
- **WHEN** condition is "value == 0 and current_hour > 8 and current_hour < 18"
- **THEN** the alert only triggers for zero values during business hours (9-17)
