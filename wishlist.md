# Long term wishes

## Add pagination to MCP tools
  - Currently all results returned at once, can hit Claude's token limits
  - Add pagination parameters (offset, limit) to tools that return large datasets:
    - `list_tables()` - for databases with many tables
    - `sample_table()` - already has limit but could add offset
    - `execute_query()` - for large query results
    - `describe_table()` - for tables with many columns/foreign keys
  - Consider default page sizes and max limits per tool

## GitHub actions for CI 
- Create a CI pipeline using GitHub Actions that runs pytest
- Investigate if we can have a packaging step for easy distribution

## More elaborate MCP type annotations
- Add tool parameter metadata (https://gofastmcp.com/servers/tools#parameter-metadata)
