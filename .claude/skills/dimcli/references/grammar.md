# DSL Grammar Reference

## Sources

| Source | Description |
|--------|-------------|
| `publications` | Journal articles, book chapters, preprints |
| `grants` | Research funding grants |
| `patents` | Patent records |
| `clinical_trials` | Clinical trial registrations |
| `datasets` | Research datasets |
| `researchers` | Researcher profiles |
| `organizations` | Research organisations |
| `policy_documents` | Policy and grey literature |
| `reports` | Technical reports |
| `source_titles` | Journals and other source titles |

## Key Fields by Source

**publications** — `id`, `title`, `year`, `doi`, `abstract`, `authors`, `journal`, `times_cited`, `open_access`, `research_orgs`, `funders`, `concepts`, `dimensions_url`, `type`, `volume`, `issue`, `pages`, `date`

**grants** — `id`, `title`, `abstract`, `start_year`, `end_date`, `funding_usd`, `funder_org_name`, `investigators`, `research_orgs`, `concepts`, `dimensions_url`, `active_status`

**patents** — `id`, `title`, `abstract`, `year`, `assignee_names`, `inventor_names`, `granted_year`, `times_cited`, `jurisdiction`, `dimensions_url`

**clinical_trials** — `id`, `title`, `brief_title`, `phase`, `overall_status`, `start_date`, `end_date`, `conditions`, `interventions`, `researchers`, `dimensions_url`

**datasets** — `id`, `title`, `description`, `date`, `authors`, `doi`, `dimensions_url`

**researchers** — `id`, `first_name`, `last_name`, `orcid_id`, `total_publications`, `total_grants`, `research_orgs`, `dimensions_url`

**organizations** — `id`, `name`, `city_name`, `country_name`, `country_code`, `dimensions_url`

**policy_documents** — `id`, `title`, `year`, `publisher_org`, `dimensions_url`

**reports** — `id`, `title`, `abstract`, `date`, `authors`, `doi`, `dimensions_url`

## Common Filter Patterns

```dsl
where year = 2023
where year in [2020:2023]
where times_cited > 100
where journal.title = "Nature"
where research_orgs.name = "University of Oxford"
where funder_org_name = "Wellcome Trust"
where open_access.type = "gold"
where category_for.name = "0601 Biochemistry and Cell Biology"
```

## Keyword Search

```dsl
search publications for "CRISPR gene editing" return publications[id+title+year] limit 10
search publications in title_abstract_only for "machine learning" return publications[id+title] limit 20
```

## Sorting, Limits, Facets

```dsl
return publications[id+title+year+times_cited] sort by times_cited limit 10
return grants[id+title+funding_usd] sort by funding_usd limit 5

# Facet / aggregation
search publications for "malaria" return year
search grants where funder_org_name = "NIH" return research_orgs limit 20
```

## Example Queries

```bash
# Recent high-impact publications
dimcli -q "search publications for \"malaria\" where year > 2020 return publications[id+title+year+journal+times_cited] sort by times_cited limit 10"

# Grants by funder
dimcli -q "search grants for \"Alzheimer\" where funder_org_name = \"NIH\" return grants[id+title+start_year+funding_usd] sort by funding_usd limit 10"

# Clinical trials
dimcli -q "search clinical_trials for \"type 2 diabetes\" where overall_status = \"Completed\" return clinical_trials[id+title+phase+start_date+end_date] limit 10"

# Publications from an organisation
dimcli -q "search publications where research_orgs.name = \"Wellcome Sanger Institute\" and year = 2023 return publications[id+title+journal+doi] limit 20"

# Top journals for a topic (facet)
dimcli -q "search publications for \"CRISPR\" return source_title limit 10"
```
