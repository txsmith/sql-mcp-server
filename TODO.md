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

- [ ] **Optimize output format for token efficiency (human-readable)**
  - FastMCP currently returns JSON, which is verbose for tabular data
  - Explore more compact human-readable formats:
    - **CSV/TSV** - for tabular query results and table samples
    - **Markdown tables** - structured but readable
    - **YAML** - often more compact than JSON for nested data
    - **Custom delimited formats** - pipe-separated or similar
    - **Condensed JSON** - remove whitespace, shorter field names
  - Could significantly reduce token usage for database results
  - Must remain human-readable for Claude to process
