# Plan: Improve list_tables Tool with Pagination

## Current Issues
- Uses SQLAlchemy inspector API with multiple synchronous calls in loops
- No pagination support
- Inefficient for large databases with many schemas/tables

## Proposed Changes

### 1. Add Pagination Parameters to Tool Interface
- Add `limit` parameter (default: 500)
- Add `page` parameter (default: 1) 
- Enforce `limit` never exceeds `max_rows_per_query` from config
- Update main.py tool registration to include new parameters

### 2. New Data Models
- Keep existing `SchemaInfo` and `TablesResponse` models
- Add pagination fields to `TablesResponse`: 
  - `total_count`: Total number of tables across all schemas
  - `current_page`: Current page number (1-based)
  - `total_pages`: Total number of pages available
- Modify response structure to be flat list of schema+table pairs rather than hierarchical

### 3. Refactor list_tables.py Core Logic
- Add dialect detection helper function to determine database type
- Implement query template system using the provided schema_table_queries.md
- Create query formatting function to handle parameter substitution, make sure it isn't suceptible to sql injection!
- Replace inspector-based approach with database_manager.execute_query
- Update response model to include pagination metadata

### 4. Query Implementation
- Create dialect-specific query mapping based on database_manager.config.databases[db_label].type
- Handle parameter substitution for {schema_name}, {limit}, {offset}
- Calculate offset from page number: `offset = (page - 1) * limit`
- Special handling for SQL Server's different OFFSET syntax
- Handle optional schema filtering (NULL when not specified)

### 5. Pagination Logic
- Validate `limit` parameter against `max_rows_per_query` config setting
- If `limit` > `max_rows_per_query`, clamp to `max_rows_per_query`
- Calculate total count with separate COUNT query for accurate pagination
- Calculate `total_pages = ceil(total_count / limit)`

### 6. Error Handling
- Maintain existing ListTablesError for consistency
- Add specific error handling for unsupported database types
- Handle edge cases like empty results gracefully
- Validate page number > 0

### 7. Update Tests
- Add tests for pagination parameters and limits
- Test different database types (currently only SQLite in tests)
- Test schema filtering functionality
- Test error conditions
- Test pagination metadata accuracy

### 8. Key Technical Details
- Use `database_manager.execute_query()` instead of inspector operations
- Get database type from `db_manager.config.databases[database].type`
- Handle both sync and async database connections (already handled by execute_query)
- Return results in consistent format across all database types
- Get `max_rows_per_query` from `db_manager.config.settings.get("max_rows_per_query", 1000)`

## Benefits
- Single efficient SQL query instead of multiple inspector calls
- Proper pagination support for large datasets with configurable limits
- Consistent performance across all database types
- More scalable architecture
- Pagination metadata for UI/client integration
