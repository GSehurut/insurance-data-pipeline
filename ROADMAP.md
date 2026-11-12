# Roadmap

Items marked **good first issue** are well scoped for new contributors. Comment on or open an issue before starting.

## 0.2: more data types

- [ ] **Claims bordereau schema** (claim reference, loss date, paid, outstanding, recoveries)
- [ ] **Premium transactions schema** with transaction types and a sign convention check
- [ ] Mapping to the **Lloyd's Coverholder Reporting Standards** field names for risk and claims bordereaux
- [ ] Full ISO 4217 currency and ISO 3166 country lists as optional data **(good first issue)**

## 0.3: pipelines and storage

- [ ] **Reconciliation helpers:** compare a bordereau's totals to a control total and report the difference **(good first issue)**
- [ ] Write validated data to **Parquet / Delta** with load metadata (source file, load time, pipeline version)
- [ ] **Microsoft Fabric example:** bronze to silver notebook using these validators and an idempotent Delta `MERGE`
- [ ] Incremental loads keyed on the schema grain

## Validation

- [ ] Configurable rules per source (for example, allow negative premium only for return premium transaction types)
- [ ] HTML or Markdown validation report for sharing with coverholders **(good first issue)**
- [ ] Warn (rather than fail) severity level for rules
- [ ] Optional integration with pandera schemas

## Synthetic data

- [ ] Synthetic claims bordereaux linked to synthetic risks
- [ ] More realistic error patterns (merged cells, totals rows, header offsets) **(good first issue)**
- [ ] Synthetic multi-currency, multi-coverholder datasets for teaching

## Done

- [x] Canonical risk bordereau schema
- [x] YAML column mappings, case and whitespace insensitive
- [x] Row level validation report (types, required values, currencies, countries, date order, duplicates)
- [x] Currency conversion with explicit rates and missing rate errors
- [x] Synthetic bordereaux with optional injected errors
- [x] `idp validate` and `idp generate` command line tools
