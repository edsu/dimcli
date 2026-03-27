# Dimensions URL Patterns

Append the record `id` to the base URL to construct a full link.

| Source | Base URL |
|--------|----------|
| `publications` | `https://app.dimensions.ai/details/publication/` |
| `grants` | `https://app.dimensions.ai/details/grant/` |
| `patents` | `https://app.dimensions.ai/details/patent/` |
| `clinical_trials` | `https://app.dimensions.ai/details/clinical_trial/` |
| `datasets` | `https://app.dimensions.ai/details/data_set/` |
| `reports` | `https://app.dimensions.ai/details/technical_report/` |
| `policy_documents` | `https://app.dimensions.ai/details/policy_documents/` |
| `researchers` | `https://app.dimensions.ai/discover/publication?and_facet_researcher=` |
| `organizations` | `https://app.dimensions.ai/discover/publication?and_facet_research_org=` |
| `source_titles` | `https://app.dimensions.ai/discover/publication?and_facet_source_title=` |
| `university_groups` | `https://app.dimensions.ai/discover/publication?and_facet_research_org_group=` |
| `funder_groups` | `https://app.dimensions.ai/discover/publication?and_facet_funder_group=` |

## Organization as Funder URLs

When an organization acts as a **funder** (rather than a research org), use `or_facet_funder=` with the GRID ID:

| Source | Funder URL pattern |
|--------|-------------------|
| `publications` | `https://app.dimensions.ai/discover/publication?or_facet_funder=` |
| `grants` | `https://app.dimensions.ai/discover/grant?or_facet_funder=` |
| `datasets` | `https://app.dimensions.ai/discover/data_set?or_facet_funder=}` |
| `clinical_trials` | `https://app.dimensions.ai/discover/clinical_trial?or_facet_funder=}` |
| `patents` | `https://app.dimensions.ai/discover/patent?or_facet_funder=` |
| `reports` | `https://app.dimensions.ai/discover/policy_document?or_facet_funder=` |
