---
name: dimcli
description: Query the Dimensions Analytics API using the dimcli CLI tool. Use when the user wants to search or retrieve data from Dimensions — publications, grants, patents, clinical trials, datasets, researchers, organisations, policy documents, or reports. Triggers on requests like "search Dimensions for...", "find publications about...", "look up grants on...", "query the Dimensions API", or "/dimcli".
---

# Dimcli Skill

Query the Dimensions Analytics API via `dimcli -q "..."` and present results with clickable Dimensions URLs.

## Workflow

1. Identify the source and intent from the user's request
2. Construct a valid DSL query — always include `id` so URLs can be built
3. Run: `dimcli -q "<query>" -f json`
4. Parse JSON and present a numbered list with title, key metadata, and Dimensions URL
5. Offer follow-ups: refine, export to CSV, fetch more records

If unsure about available fields, run `dimcli -q "describe schema"` first.

**DSL grammar and URL patterns:** See [grammar.md](references/grammar.md) and [urls.md](references/urls.md).

## Query Structure

```
search <source> [for "<keywords>"] [where <filters>] return <source>[field1+field2+...] [limit N] [sort by <field>]
```

Always include `id` in return fields. Use `[basics]` for a standard field set.

## Output Format

Present results as a numbered list:

```
1. **Title of the work** (2023)
   Journal: Nature | Cited by: 142
   https://app.dimensions.ai/details/publication/pub.1234567890

2. ...
```

Summarise after the list: total found, date range, notable patterns.

## Flags

| Flag | Use case |
|------|----------|
| `-f json` | Default — structured data |
| `-f csv --nice` | Clean tabular export |
| `-f df` | Formatted terminal table |
| `-f df --html` | HTML table with hyperlinks |

## Advanced

- **Large results**: API returns max 1000/call (50k with pagination). Suggest narrowing filters or using `query_iterative()` in Python.
- **Schema lookup**: `dimcli -q "describe schema"`
- **Export**: `dimcli -q "..." -f csv --nice > results.csv`

---

## Subcommand: `profile <grid_id>`

Generate a full profile report for an organisation, given its GRID ID (format: `grid.XX`).

### Workflow

Run all queries **sequentially** (never in parallel — concurrent calls cause session conflicts).

**Step 1 — Fetch organisation metadata:**

```bash
dimcli -q "search organizations where id = \"<grid_id>\" return organizations[acronym+city_name+country_code+country_name+dimensions_url+established+external_ids_fundref+hierarchy_details+id+isni_ids+latitude+linkout+longitude+name+organization_child_ids+organization_parent_ids+organization_related_ids+ror_ids+status+types+ultimate_parent_id+wikidata_ids+wikipedia_url]" -f json 2>/dev/null
```

> Note: `organizations[all]` is **not valid** — always enumerate fields explicitly.

**Step 2 — Count documents per source:**

Run each query below sequentially. Extract `_stats.total_count` from the JSON.

```bash
# Publications
dimcli -q "search publications where research_orgs = \"<grid_id>\" return publications limit 1" -f json 2>/dev/null

# Grants
dimcli -q "search grants where research_orgs = \"<grid_id>\" return grants limit 1" -f json 2>/dev/null

# Datasets
dimcli -q "search datasets where research_orgs = \"<grid_id>\" return datasets limit 1" -f json 2>/dev/null

# Clinical Trials
dimcli -q "search clinical_trials where research_orgs = \"<grid_id>\" return clinical_trials limit 1" -f json 2>/dev/null

# Patents — NOTE: uses 'assignees', not 'research_orgs'
dimcli -q "search patents where assignees = \"<grid_id>\" return patents limit 1" -f json 2>/dev/null

# Reports
dimcli -q "search reprots where research_orgs = \"<grid_id>\" return reports limit 1" -f json 2>/dev/null

# Policy Documents — NOTE: uses 'publisher_org', not 'research_orgs'
dimcli -q "search policy_documents where publisher_org = \"<grid_id>\" return policy_documents limit 1" -f json 2>/dev/null
```

> Each source uses a different field name to filter by organisation:
> | Source | Filter field |
> |--------|-------------|
> | publications, grants, datasets, clinical_trials | `research_orgs` |
> | patents | `assignees` |
> | policy_documents | `publisher_org` |

**Step 2b — Count documents where org is a funder:**

```bash
# Publications (as funder)
dimcli -q "search publications where funders = \"<grid_id>\" return publications limit 1" -f json 2>/dev/null

# Grants (as funder) — NOTE: uses 'funder_orgs', not 'funders'
dimcli -q "search grants where funder_orgs = \"<grid_id>\" return grants limit 1" -f json 2>/dev/null

# Datasets (as funder)
dimcli -q "search datasets where funders = \"<grid_id>\" return datasets limit 1" -f json 2>/dev/null

# Clinical Trials (as funder)
dimcli -q "search clinical_trials where funders = \"<grid_id>\" return clinical_trials limit 1" -f json 2>/dev/null

# Patents (as funder)
dimcli -q "search patents where funders = \"<grid_id>\" return patents limit 1" -f json 2>/dev/null

# Reports (as funder) — NOTE: uses 'funder_orgs', not 'funders'
dimcli -q "search reports where funder_orgs = \"<grid_id>\" return reports limit 1" -f json 2>/dev/null
```

**Step 3 — Piping to Python:**

Always redirect stderr with `2>/dev/null` before piping to Python. The CLI prints
`"Reusing cached session."` to stdout, which breaks JSON parsing if included.

```bash
dimcli -q "..." -f json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['_stats']['total_count'])"
```

### Output Format

Print the profile as a markdown report:

```markdown
# Organisation Profile: <Name> (<acronym>)

**GRID ID:** `<id>` | **Status:** <status> | **Type:** <types> | **Established:** <year>

## Location
- City: <city>, <country>
- Coordinates: <lat>, <lon>

## Links
- Website: <linkout>
- Wikipedia: <wikipedia_url>
- Dimensions: <dimensions_url>

## External Identifiers
- ROR: <ror_ids>
- ISNI: <isni_ids>
- Wikidata: <wikidata_ids>
- FundRef IDs: <external_ids_fundref>

## Hierarchy
- Ultimate parent: <ultimate_parent_id>
- Parent orgs: <organization_parent_ids>
- Child orgs: <organization_child_ids>
- Related orgs: <organization_related_ids>

## Document Counts (as Research Org)
| Source | Count | Dimensions URL |
|--------|------:|----------------|
| Publications | N | https://app.dimensions.ai/discover/publication?and_facet_research_org=<grid_id> |
| Grants | N | https://app.dimensions.ai/discover/grant?search_mode=content&or_facet_research_org=<grid_id> |
| Datasets | N | https://app.dimensions.ai/discover/dataset?and_facet_research_org=<grid_id> |
| Clinical Trials | N | https://app.dimensions.ai/discover/clinical_trial?and_facet_research_org=<grid_id> |
| Patents | N | https://app.dimensions.ai/discover/patent?and_facet_research_org=<grid_id> |
| Reports | N | https://app.dimensions.ai/discover/technical_report?and_facet_research_org=<grid_id> |
| Policy Documents | N | https://app.dimensions.ai/discover/policy_document?and_facet_research_org=<grid_id> |
| **Total** | **N** | |

## Document Counts (as Funder)
| Source | Count | Dimensions URL |
|--------|------:|----------------|
| Publications | N | https://app.dimensions.ai/discover/publication?or_facet_funder=<grid_id> |
| Grants | N | https://app.dimensions.ai/discover/grant?or_facet_funder=<grid_id> |
| Datasets | N | https://app.dimensions.ai/discover/data_set?or_facet_funder=<grid_id> |
| Clinical Trials | N | https://app.dimensions.ai/discover/clinical_trial?or_facet_funder=<grid_id> |
| Patents | N | https://app.dimensions.ai/discover/patent?or_facet_funder=<grid_id> |
| Reports | N | https://app.dimensions.ai/discover/technical_report?or_facet_funder=<grid_id> |
| **Total** | **N** | |
```

### Export

If the user asks to export, save the report to `<grid_id>_profile.md` using the Write tool.
Confirm the file path after saving.
