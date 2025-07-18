# Table Column Listing Queries

This document contains SQL queries to list table columns with metadata for a specific table across all supported database dialects with configurable limit and offset parameters.

## PostgreSQL

```sql
SELECT 
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog')
AND c.table_name = '{table_name}'
AND ('{schema_name}' IS NULL OR c.table_schema = '{schema_name}')
ORDER BY c.ordinal_position
LIMIT {limit} OFFSET {offset}
```

## MySQL

```sql
SELECT 
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
AND c.table_name = '{table_name}'
AND ('{schema_name}' IS NULL OR c.table_schema = '{schema_name}')
ORDER BY c.ordinal_position
LIMIT {limit} OFFSET {offset}
```

## SQLite

```sql
SELECT 
    p.name as column_name,
    p.type as data_type,
    CASE WHEN p."notnull" = 0 THEN 'YES' ELSE 'NO' END as is_nullable,
    p.dflt_value as column_default
FROM pragma_table_info('{table_name}') p
ORDER BY p.cid
LIMIT {limit} OFFSET {offset}
```

## SQL Server

```sql
SELECT 
    c.name as column_name,
    tp.name as data_type,
    CASE WHEN c.is_nullable = 1 THEN 'YES' ELSE 'NO' END as is_nullable,
    dc.definition as column_default
FROM sys.tables t
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
INNER JOIN sys.columns c ON t.object_id = c.object_id
INNER JOIN sys.types tp ON c.user_type_id = tp.user_type_id
LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
WHERE s.name NOT IN ('information_schema', 'sys')
AND t.name = '{table_name}'
AND ('{schema_name}' IS NULL OR s.name = '{schema_name}')
ORDER BY c.column_id
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
```

## Snowflake

```sql
SELECT 
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_schema NOT IN ('INFORMATION_SCHEMA')
AND c.table_name = '{table_name}'
AND ('{schema_name}' IS NULL OR c.table_schema = '{schema_name}')
ORDER BY c.ordinal_position
LIMIT {limit} OFFSET {offset}
```

## Column Information Returned

Each query returns the following columns:
- `column_name`: The column name
- `data_type`: The column data type
- `is_nullable`: Whether the column allows NULL values ('YES' or 'NO')
- `column_default`: The default value for the column

## Usage Notes

- Replace `{table_name}`, `{schema_name}`, `{limit}`, and `{offset}` with actual values
- `{schema_name}` is optional - set to `NULL` if not filtering by schema
- Default pagination: `LIMIT 100 OFFSET 0` for first page
- SQL Server uses different syntax: `OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY`
- Each query excludes system schemas/tables to focus on user data
- Results are ordered by column position for consistent pagination
- SQLite doesn't use schemas, so `schema_name` is ignored
