# Schema + Table Listing Queries

This document contains SQL queries to list schema+table pairs for each supported database dialect with configurable limit and offset parameters.

## PostgreSQL

```sql
SELECT schemaname as schema_name, tablename as table_name
FROM pg_tables
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
AND ('{schema_name}' IS NULL OR schemaname = '{schema_name}')
ORDER BY schemaname, tablename
LIMIT {limit} OFFSET {offset}
```

## MySQL

```sql
SELECT table_schema as schema_name, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
AND table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
AND ('{schema_name}' IS NULL OR table_schema = '{schema_name}')
ORDER BY table_schema, table_name
LIMIT {limit} OFFSET {offset}
```

## SQLite

```sql
SELECT 'main' as schema_name, name as table_name
FROM sqlite_master
WHERE type = 'table'
AND name NOT LIKE 'sqlite_%'
ORDER BY name
LIMIT {limit} OFFSET {offset}
```

## SQL Server

```sql
SELECT s.name as schema_name, t.name as table_name
FROM sys.tables t
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name NOT IN ('information_schema', 'sys')
AND ('{schema_name}' IS NULL OR s.name = '{schema_name}')
ORDER BY s.name, t.name
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
```

## Snowflake

```sql
SELECT table_schema as schema_name, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
AND table_schema NOT IN ('INFORMATION_SCHEMA')
AND ('{schema_name}' IS NULL OR table_schema = '{schema_name}')
ORDER BY table_schema, table_name
LIMIT {limit} OFFSET {offset}
```

## Usage Notes

- Replace `{schema_name}`, `{limit}`, and `{offset}` with actual values
- `{schema_name}` is optional - set to `NULL` if not filtering by schema
- Default pagination: `LIMIT 100 OFFSET 0` for first page
- SQL Server uses different syntax: `OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY`
- Each query excludes system schemas/tables to focus on user data
- Results are ordered by schema name, then table name for consistent pagination
- SQLite doesn't use schemas, so `schema_name` parameter is ignored