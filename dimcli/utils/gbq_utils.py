#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
BigQuery schema exploration utilities for dimcli
"""

import click

try:
    from google.cloud import bigquery
    GBQ_AVAILABLE = True
except ImportError:
    GBQ_AVAILABLE = False


# Default BigQuery project and dataset
DEFAULT_PROJECT = 'dimensions-ai'
DEFAULT_DATASET = 'data_analytics'

_cached_client = None


def get_gbq_client(project_id=None):
    """
    Get BigQuery client with config-based or default credentials

    Args:
        project_id: Optional project ID override. Defaults to 'dimensions-ai'

    Returns:
        google.cloud.bigquery.Client instance

    Raises:
        ImportError: If google-cloud-bigquery is not installed
        Exception: If credentials are invalid
    """
    global _cached_client

    if not GBQ_AVAILABLE:
        raise ImportError(
            "google-cloud-bigquery is not installed.\n"
            "Install it with: pip install google-cloud-bigquery"
        )

    if _cached_client is not None and project_id is None:
        return _cached_client

    # Try to get project_id from config if not provided
    if project_id is None:
        from ..core.auth import get_gbq_project_id
        project_id = get_gbq_project_id()

    # Use default project if still not set
    if project_id is None:
        project_id = DEFAULT_PROJECT

    try:
        client = bigquery.Client(project=project_id)

        # Cache the client
        _cached_client = client

        return client

    except Exception as e:
        raise Exception(
            f"Failed to create BigQuery client: {str(e)}\n"
            "Please check your GCP credentials and project configuration.\n"
            "Set GOOGLE_APPLICATION_CREDENTIALS environment variable or use 'gcloud auth application-default login'"
        )


def list_tables(client, dataset_id=None, search_term=None):
    """
    List BigQuery tables, optionally filtered by dataset or search term

    Args:
        client: BigQuery client instance
        dataset_id: Optional dataset ID to filter by. Defaults to 'data_analytics'
        search_term: Optional search term to filter table names (searches only table name)

    Returns:
        List of dicts with table info: {'name', 'dataset', 'project', 'type', 'last_modified', 'full_path'}
    """
    try:
        project_id = client.project

        # Use dataset from config if available, otherwise use default
        if dataset_id is None:
            from ..core.auth import get_gbq_dataset_id
            dataset_id = get_gbq_dataset_id()
            if dataset_id is None:
                dataset_id = DEFAULT_DATASET

        # Get tables from the specified dataset
        tables = []
        try:
            dataset_tables = client.list_tables(dataset_id)
            for table in dataset_tables:
                table_obj = client.get_table(table.reference)
                full_path = f"{project_id}.{dataset_id}.{table.table_id}"
                tables.append({
                    'project': project_id,
                    'dataset': dataset_id,
                    'name': table.table_id,
                    'type': table.table_type,
                    'last_modified': table_obj.modified,
                    'full_path': full_path
                })
        except Exception as e:
            raise Exception(f"Failed to access dataset '{dataset_id}': {str(e)}")

        # Filter by search term if provided (search only table name)
        if search_term:
            search_lower = search_term.lower()
            tables = [t for t in tables if search_lower in t['name'].lower()]

        return tables

    except Exception as e:
        raise Exception(f"Failed to list tables: {str(e)}")


def list_fields(client, table_name=None, dataset_id=None, search_term=None):
    """
    List fields for a table or search across all tables in a dataset

    Args:
        client: BigQuery client instance
        table_name: Optional table name (format: dataset.table or just table)
        dataset_id: Optional dataset ID. Defaults to 'data_analytics'
        search_term: Optional search term to filter field names

    Returns:
        List of dicts with field info: {'table', 'dataset', 'field', 'type', 'mode', 'description'}
    """
    try:
        project_id = client.project

        # Use dataset from config if available, otherwise use default
        if dataset_id is None:
            from ..core.auth import get_gbq_dataset_id
            dataset_id = get_gbq_dataset_id()
            if dataset_id is None:
                dataset_id = DEFAULT_DATASET

        if table_name:
            # Parse table name
            if '.' in table_name:
                dataset_id, table_id = table_name.split('.', 1)
            else:
                # Use default dataset
                table_id = table_name

            # Get table schema
            table_ref = f"{project_id}.{dataset_id}.{table_id}"
            table = client.get_table(table_ref)

            fields = []
            for field in table.schema:
                fields.append({
                    'project': project_id,
                    'dataset': dataset_id,
                    'table': table_id,
                    'field': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'description': field.description or ''
                })

            # Filter by search term if provided
            if search_term:
                search_lower = search_term.lower()
                fields = [f for f in fields if search_lower in f['field'].lower()
                         or search_lower in f.get('description', '').lower()]

            return fields

        else:
            # List fields across all tables in the default dataset
            all_fields = []
            try:
                tables = client.list_tables(dataset_id)
                for table_item in tables:
                    table = client.get_table(table_item.reference)
                    for field in table.schema:
                        all_fields.append({
                            'project': project_id,
                            'dataset': dataset_id,
                            'table': table.table_id,
                            'field': field.name,
                            'type': field.field_type,
                            'mode': field.mode,
                            'description': field.description or ''
                        })
            except Exception as e:
                raise Exception(f"Failed to access dataset '{dataset_id}': {str(e)}")

            # Filter by search term if provided
            if search_term:
                search_lower = search_term.lower()
                all_fields = [f for f in all_fields if search_lower in f['field'].lower()
                             or search_lower in f['table'].lower()
                             or search_lower in f.get('description', '').lower()]

            return all_fields

    except Exception as e:
        raise Exception(f"Failed to list fields: {str(e)}")


def print_tables(tables_data):
    """
    Pretty print tables list in tabular format

    Args:
        tables_data: List of table dicts from list_tables()
    """
    if not tables_data:
        click.secho("No tables found.", dim=True)
        return

    # Get project and dataset from first table
    project = tables_data[0]['project'] if tables_data else ''
    dataset = tables_data[0]['dataset'] if tables_data else ''

    click.echo()
    click.secho(f"BIGQUERY TABLES ({len(tables_data)} found)", bold=True)
    click.secho(f"Dataset: {project}.{dataset}", dim=True)
    click.echo()

    # Sort tables by name
    sorted_tables = sorted(tables_data, key=lambda x: x['name'])

    # Calculate column widths
    max_name_len = max(len(t['name']) for t in sorted_tables)
    max_path_len = max(len(t['full_path']) for t in sorted_tables)

    # Set minimum column widths
    name_width = max(max_name_len, 15)
    modified_width = 20  # Fixed width for timestamp
    path_width = max(max_path_len, 40)

    # Print header
    header = f"{'Table Name':<{name_width}}  {'Last Updated':<{modified_width}}  {'Full Path':<{path_width}}"
    click.secho(header, bold=True)
    click.secho('-' * len(header), dim=True)

    # Print each table row
    for table in sorted_tables:
        name = table['name']
        # Format timestamp
        modified = table['last_modified']
        if modified:
            # Format as YYYY-MM-DD HH:MM:SS
            modified_str = modified.strftime('%Y-%m-%d %H:%M:%S')
        else:
            modified_str = 'N/A'

        full_path = table['full_path']

        # Create row with proper spacing (no colors to avoid alignment issues)
        click.echo(
            click.style(f"{name:<{name_width}}", fg='blue') + "  " +
            f"{modified_str:<{modified_width}}" + "  " +
            click.style(full_path, fg='green')
        )

    click.echo()
    click.secho(f"Total: {len(sorted_tables)} tables", dim=True)
    click.echo()


def print_fields(fields_data, search_term=None):
    """
    Pretty print fields list using click.secho()

    Args:
        fields_data: List of field dicts from list_fields()
        search_term: Optional search term to display in header
    """
    if not fields_data:
        if search_term:
            click.secho(f"No fields found matching '{search_term}'.", dim=True)
        else:
            click.secho("No fields found.", dim=True)
        return

    # Get project and dataset from first field
    project = fields_data[0]['project'] if fields_data else ''
    dataset = fields_data[0]['dataset'] if fields_data else ''

    # Check if all fields are from the same table
    tables = set(f['table'] for f in fields_data)
    single_table = tables.pop() if len(tables) == 1 else None

    click.secho(f"\n{'='*60}", dim=True)
    if search_term and single_table:
        click.secho(f"FIELD SEARCH in {single_table} ({len(fields_data)} found matching '{search_term}')", bold=True)
    elif search_term:
        click.secho(f"FIELD SEARCH RESULTS ({len(fields_data)} found matching '{search_term}')", bold=True)
    elif single_table:
        click.secho(f"FIELDS in {single_table} ({len(fields_data)} fields)", bold=True)
    else:
        click.secho(f"BIGQUERY FIELDS ({len(fields_data)} found)", bold=True)
    click.secho(f"Dataset: {project}.{dataset}", dim=True)
    click.secho(f"{'='*60}\n", dim=True)

    # Group by table for better readability
    current_table = None
    for field in sorted(fields_data, key=lambda x: (x['table'], x['field'])):
        table_name = field['table']

        # Print table header if it's a new table (only if multiple tables)
        if current_table != table_name:
            if current_table is not None:
                click.echo()  # Separator between tables
            # Only show table header if we have multiple tables
            if not single_table:
                click.secho(f"Table: {table_name}", bold=True, fg='blue')
            current_table = table_name

        # Format: field_name [TYPE MODE] description
        field_info = f"[{field['type']}"
        if field.get('mode') and field['mode'] != 'NULLABLE':
            field_info += f" {field['mode']}"
        field_info += "]"

        # Adjust indentation: single table = no indent, multiple tables = indent
        indent = "" if single_table else "  "

        click.echo(
            indent + click.style(field['field'], fg='green') + " " +
            click.style(field_info, dim=True)
        )

        if field.get('description'):
            click.echo(indent + "  " + click.style(field['description'], dim=True))

    click.echo()  # Final newline
    click.secho(f"{'='*60}", dim=True)
