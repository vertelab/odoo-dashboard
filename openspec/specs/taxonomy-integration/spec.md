## ADDED Requirements

### Requirement: XBRL taxonomy import
The system SHALL import Swedish XBRL taxonomies from taxonomier.se into dashboard.taxonomy_concept records.

#### Scenario: Import K2 taxonomy
- **WHEN** the taxonomy importer processes a K2 annual report XBRL file
- **THEN** concepts like "Nettoomsättning", "Rörelseresultat", "Balansomslutning" are created with their Swedish labels, data types, balance (debit/credit), and law references (ÅRL, BFNAR)

#### Scenario: Hierarchical relationships
- **WHEN** concepts have parent-child summation relationships in XBRL
- **THEN** taxonomy_concept records are linked via parent_id, enabling auto-generation of P&L and balance sheet dashboards

### Requirement: Taxonomy to Odoo account_type mapping
The system SHALL provide a configurable mapping from taxonomy concepts to Odoo account.account types.

#### Scenario: Income concept mapping
- **WHEN** the taxonomy concept "Nettoomsättning" is mapped to account_type=["income", "income_other"]
- **THEN** a metric with taxonomy_ref="se-gaap.Nettoomsattning" can auto-generate its SQL/ORM query from the mapping

#### Scenario: Default K2 mappings
- **WHEN** dashboard_vrtl_taxonomy is installed
- **THEN** default mappings for all standard K2 concepts are created (income→income/income_other, expense→expense, etc.)

### Requirement: Metric auto-generation from taxonomy
The system SHALL enable AI or users to generate dashboard.metric records by referencing taxonomy concepts.

#### Scenario: Generate metric from concept
- **WHEN** user creates a metric referencing taxonomy concept "Nettoomsättning"
- **THEN** the metric's label, unit, and default domain are populated from the concept and its account_type mapping

#### Scenario: AI-assisted metric creation
- **WHEN** AI skill processes "Jag vill se rörelseresultat per månad"
- **THEN** it looks up "Rörelseresultat" in taxonomy_concept, finds the account_type mapping, and generates a metric with appropriate SQL/ORM query

### Requirement: Taxonomy multi-language support
The system SHALL store both Swedish and English labels for each taxonomy concept.

#### Scenario: Swedish label display
- **WHEN** user language is Swedish
- **THEN** dashboard charts display "Nettoomsättning" as the metric label

#### Scenario: English label display
- **WHEN** user language is English (or en_US)
- **THEN** dashboard charts display "Net Revenue" as the metric label
