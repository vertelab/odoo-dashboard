## ADDED Requirements

### Requirement: Three cache layers
The system SHALL provide three caching layers: request-cache (dict, per HTTP request), session-cache (dashboard.cache ORM, TTL-based), and shared-cache (only for safe_for_shared_cache metrics).

#### Scenario: Request-cache prevents duplicate queries
- **WHEN** two charts on the same dashboard use the same metric with identical filters
- **THEN** the metric's data is fetched once; both charts render from the same in-memory result

#### Scenario: Session-cache serves auto-refresh
- **WHEN** a dashboard auto-refreshes and the session-cache entry is still valid (within TTL)
- **THEN** no database query is executed; cached data is returned immediately

### Requirement: User-aware cache keys
The system SHALL include user_id in the cache key for all metrics with row_level_security=True.

#### Scenario: Different users get different cache entries
- **WHEN** CFO and Sales Manager both view the same dashboard with row_level_security=True metrics
- **THEN** separate cache entries are created (different user_id in key); each sees only their authorized data

#### Scenario: Shared cache for non-row-level metrics
- **WHEN** a metric has safe_for_shared_cache=True and two users view it with identical filters
- **THEN** a SINGLE cache entry is shared between them (no user_id in key)

### Requirement: Configurable TTL per dashboard type
The system SHALL support TTL configuration: operational (30-60s), tactical (2-5min), strategic (5-15min), financial (15-60min).

#### Scenario: Operational dashboard cache expires quickly
- **WHEN** an inventory dashboard has TTL=60s
- **THEN** cache entries expire after 60 seconds; next auto-refresh fetches fresh data

#### Scenario: Financial dashboard cache persists longer
- **WHEN** a CFO P&L dashboard has TTL=900s (15min)
- **THEN** cache entries persist for 15 minutes, reducing database load for rarely-changing financial data

### Requirement: Manual cache invalidation
The system SHALL allow users to force-refresh, bypassing all cache layers.

#### Scenario: User clicks refresh
- **WHEN** user clicks the "Refresh" button on a dashboard
- **THEN** all charts ignore cache and fetch fresh data; new results replace the cache entries

### Requirement: Cache cleanup
The system SHALL run periodic cleanup of expired and cold cache entries via ir.cron.

#### Scenario: Expired entries removed
- **WHEN** the cleanup cron runs (every 15 minutes)
- **THEN** all dashboard.cache records with expires_at < NOW() are deleted

#### Scenario: Overflow prevention
- **WHEN** a single metric has more than 1000 cache entries
- **THEN** the oldest entries beyond 1000 are deleted (ROW_NUMBER-based cleanup)
