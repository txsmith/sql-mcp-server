# Foreign Key Listing Queries

This document contains SQL queries to list foreign key relationships across all supported database dialects with configurable filtering by source and destination tables.

## Generalized Foreign Key Query

### PostgreSQL

```sql
SELECT 
    n.nspname as source_schema_name,
    t.relname as source_table_name,
    a.attname as source_column_name,
    fn.nspname as dest_schema_name,
    ft.relname as dest_table_name,
    fa.attname as dest_column_name,
    c.conname as constraint_name
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
JOIN pg_namespace n ON t.relnamespace = n.oid
JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
JOIN pg_class ft ON c.confrelid = ft.oid
JOIN pg_namespace fn ON ft.relnamespace = fn.oid
JOIN pg_attribute fa ON fa.attrelid = ft.oid AND fa.attnum = ANY(c.confkey)
WHERE c.contype = 'f'
AND ('{source_table_name}' IS NULL OR t.relname = '{source_table_name}')
AND ('{dest_table_name}' IS NULL OR ft.relname = '{dest_table_name}')
AND ('{source_schema_name}' IS NULL OR n.nspname = '{source_schema_name}')
AND ('{dest_schema_name}' IS NULL OR fn.nspname = '{dest_schema_name}')
ORDER BY c.conname
LIMIT {limit} OFFSET {offset}
```

### MySQL

```sql
SELECT 
    kcu.table_schema as source_schema_name,
    kcu.table_name as source_table_name,
    kcu.column_name as source_column_name,
    kcu.referenced_table_schema as dest_schema_name,
    kcu.referenced_table_name as dest_table_name,
    kcu.referenced_column_name as dest_column_name,
    kcu.constraint_name
FROM information_schema.key_column_usage kcu
WHERE kcu.referenced_table_name IS NOT NULL
AND kcu.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
AND ('{source_table_name}' IS NULL OR kcu.table_name = '{source_table_name}')
AND ('{dest_table_name}' IS NULL OR kcu.referenced_table_name = '{dest_table_name}')
AND ('{source_schema_name}' IS NULL OR kcu.table_schema = '{source_schema_name}')
AND ('{dest_schema_name}' IS NULL OR kcu.referenced_table_schema = '{dest_schema_name}')
ORDER BY kcu.constraint_name
LIMIT {limit} OFFSET {offset}
```

### SQLite

```sql
SELECT 
    'main' as source_schema_name,
    m.name as source_table_name,
    fk."from" as source_column_name,
    'main' as dest_schema_name,
    fk."table" as dest_table_name,
    fk."to" as dest_column_name,
    'fk_' || m.name || '_' || fk.id as constraint_name
FROM sqlite_master m
JOIN pragma_foreign_key_list(m.name) fk
WHERE m.type = 'table' AND m.name NOT LIKE 'sqlite_%'
AND ('{source_table_name}' IS NULL OR m.name = '{source_table_name}')
AND ('{dest_table_name}' IS NULL OR fk."table" = '{dest_table_name}')
ORDER BY constraint_name
LIMIT {limit} OFFSET {offset}
```

### SQL Server

```sql
SELECT 
    s.name as source_schema_name,
    t.name as source_table_name,
    c.name as source_column_name,
    rs.name as dest_schema_name,
    rt.name as dest_table_name,
    rc.name as dest_column_name,
    fk.name as constraint_name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.tables t ON fk.parent_object_id = t.object_id
JOIN sys.schemas s ON t.schema_id = s.schema_id
JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
JOIN sys.schemas rs ON rt.schema_id = rs.schema_id
JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
WHERE s.name NOT IN ('information_schema', 'sys')
AND ('{source_table_name}' IS NULL OR t.name = '{source_table_name}')
AND ('{dest_table_name}' IS NULL OR rt.name = '{dest_table_name}')
AND ('{source_schema_name}' IS NULL OR s.name = '{source_schema_name}')
AND ('{dest_schema_name}' IS NULL OR rs.name = '{dest_schema_name}')
ORDER BY fk.name
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
```

### Snowflake

```sql
SELECT 
    tc.table_schema as source_schema_name,
    tc.table_name as source_table_name,
    kcu.column_name as source_column_name,
    ccu.table_schema as dest_schema_name,
    ccu.table_name as dest_table_name,
    ccu.column_name as dest_column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema NOT IN ('INFORMATION_SCHEMA')
AND ('{source_table_name}' IS NULL OR tc.table_name = '{source_table_name}')
AND ('{dest_table_name}' IS NULL OR ccu.table_name = '{dest_table_name}')
AND ('{source_schema_name}' IS NULL OR tc.table_schema = '{source_schema_name}')
AND ('{dest_schema_name}' IS NULL OR ccu.table_schema = '{dest_schema_name}')
ORDER BY tc.constraint_name
LIMIT {limit} OFFSET {offset}
```

## Column Information Returned

Each query returns the following columns:
- `source_schema_name`: The schema of the table with the foreign key
- `source_table_name`: The table name with the foreign key
- `source_column_name`: The column name with the foreign key
- `dest_schema_name`: The schema of the referenced table
- `dest_table_name`: The referenced table name
- `dest_column_name`: The referenced column name
- `constraint_name`: The foreign key constraint name

## Usage Notes

- Replace `{source_table_name}`, `{dest_table_name}`, `{source_schema_name}`, `{dest_schema_name}`, `{limit}`, and `{offset}` with actual values
- All table and schema parameters are optional - set to `NULL` if not filtering by that parameter
- Default pagination: `LIMIT 100 OFFSET 0` for first page
- SQL Server uses different syntax: `OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY`
- SQLite doesn't use schemas, so schema parameters are ignored
- PostgreSQL uses system catalogs (`pg_constraint`, `pg_class`, etc.) for better performance

## Usage Examples

**Outgoing FKs (what `loan_applications` references):**
- Set `source_table_name = 'loan_applications'`, leave `dest_table_name` as `NULL`
- Results: `loan_applications.farmer_id` → `farmers.id`, `loan_applications.product_id` → `products.id`

**Incoming FKs (what references `loan_applications`):**
- Set `dest_table_name = 'loan_applications'`, leave `source_table_name` as `NULL`
- Results: `agrodealer_assignments.loan_application_id` → `loan_applications.id`

**Specific relationship:**
- Set both `source_table_name = 'loan_applications'` and `dest_table_name = 'farmers'`
- Results: `loan_applications.farmer_id` → `farmers.id`

**All FKs in a schema:**
- Set `source_schema_name = 'public'`, leave table names as `NULL`
- Returns all foreign key relationships where the source table is in the public schema