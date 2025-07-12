# TODO

## Configuration Improvements

- [ ] **Password management integration**
  - Integrate with `pass` utility for password storage
  - Avoid storing plaintext secrets in config files
  - Support password references like `password: "pass:database/mydb"`

## Performance & Usability

- [ ] **Add pagination to MCP tools**
  - Currently all results returned at once, can hit Claude's token limits
  - Add pagination parameters (offset, limit) to tools that return large datasets:
    - `list_tables()` - for databases with many tables
    - `sample_table()` - already has limit but could add offset
    - `execute_query()` - for large query results
    - `describe_table()` - for tables with many columns/foreign keys
  - Consider default page sizes and max limits per tool

