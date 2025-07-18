# Plan: Improve describe_table Tool with Query-Based Approach

## Current Issues
- Uses SQLAlchemy inspector API with multiple synchronous calls
- Inefficient foreign key discovery (loops through all tables)
- No pagination support for columns or foreign keys
- Performance degrades with large schemas

## Proposed Changes

### 1. Add Pagination Parameters to Tool Interface
- Add `limit` parameter (default: 250) - applies to total items (columns + FKs)
- Add `page` parameter (default: 1)
- Enforce limit never exceeds `max_rows_per_query` from config
- Update main.py tool registration to include new parameters

### 2. Enhanced Data Models
- Keep existing `ColumnInfo`, `ForeignKey`, `IncomingForeignKey` models
- Add pagination fields to `TableDescription`:
  - `total_count`: Total number of items (columns + outgoing FKs + incoming FKs)
  - `current_page`: Current page number
  - `total_pages`: Total number of pages

### 3. Refactor describe_table.py Core Logic
- Follow pattern from refactored `list_tables.py` (using DIALECT_QUERIES structure)
- Use `db_manager.get_dialect_name()` for dialect detection
- Replace inspector-based approach with database_manager.execute_query
- Split into separate functions for columns and foreign keys

### 4. Query Implementation
- Create DIALECT_QUERIES dict with separate queries for columns, incoming/outgoing FKs(the query for outgoing and incoming should be the same!)
- Use column queries from table_column_queries.md
- Use foreign key queries from foreign_key_queries.md
- Handle parameter substitution for {table_name}, {schema_name}, {limit}, {offset}
- Handle optional schema filtering (empty string when not specified)

### 5. Pagination Logic for Mixed Results
- Calculate total counts: `total_count = column_count + outgoing_fk_count + incoming_fk_count`
- Calculate `offset = (page - 1) * limit`
- Determine what to fetch based on offset:
  - If `offset < column_count`: fetch columns starting from offset
  - If `offset >= column_count && offset < column_count + outgoing_fk_count`: fetch outgoing FKs
  - If `offset >= column_count + outgoing_fk_count`: fetch incoming FKs
- Handle cases where page spans multiple data types (columns → FKs)
- Return up to `limit` items total, prioritizing: columns first, then outgoing FKs, then incoming FKs

### 6. Primary Key Detection
- Add primary key detection using information_schema queries
- Create separate primary key query templates for each dialect
- Update ColumnInfo.primary_key field based on query results
- Handle multi-column primary keys properly

### 7. Query Template System
- Create DIALECT_QUERIES structure with 'columns', 'columns_count', 'foreign_key', 'foreign_key_count', 'primary_key' queries
- Follow list_tables.py pattern: use empty string for optional parameters
- Handle SQL Server's different OFFSET syntax
- Special handling for SQLite's pragma-based queries

### 8. Pagination Logic
- Follow list_tables.py pattern for limit validation and clamping
- Validate limit parameters against `max_rows_per_query` config setting
- Get separate COUNT queries for columns, outgoing FKs, incoming FKs
- Calculate `total_count = column_count + outgoing_fk_count + incoming_fk_count`
- Calculate `total_pages = math.ceil(total_count / limit)`
- Handle edge cases like empty results gracefully

### 9. Error Handling
- Maintain existing TableNotFoundError and DescribeTableError
- Add specific error handling for unsupported database types
- Validate page numbers > 0 and limit > 0 (follow list_tables.py pattern)
- Handle table existence check via SQL query instead of inspector

### 10. Update Tests
- Follow test patterns from test_list_tables.py
- Add tests for pagination parameters and limits
- Test different database types (currently only SQLite in tests)
- Test schema filtering functionality
- Test error conditions and edge cases
- Test pagination metadata accuracy
- Test primary key detection across dialects

### 11. Key Technical Details
- Use `database_manager.execute_query()` for all operations
- Use `db_manager.get_dialect_name(database)` for dialect detection
- Get `max_rows_per_query` from `db_manager.config.settings.get("max_rows_per_query", 1000)`
- Handle both sync and async database connections
- Return consistent format across all database types
- Maintain backward compatibility with existing response structure

