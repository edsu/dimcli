#!/usr/bin/env python
"""
Autocompletion example.

Press [Tab] to complete the current word.
- The first Tab press fills in the common part of all completions
    and shows all the completions. (In the menu)
- Any following tab press cycles through all the possible completions.
"""
from __future__ import unicode_literals

from prompt_toolkit.completion import Completion, Completer
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from .autocompletion import *
from .history import *
from .key_bindings import *
from .lexer import *



# from prompt_toolkit import prompt   #using session instead


import click
import json
import sys
import os
import time
import requests

from ..core.api import Dsl
from ..core.auth import USER_HISTORY_FILE, USER_EXPORTS_DIR, do_global_login, get_global_connection
from ..core.dsl_grammar import *
from ..utils.all import *





HELP_MESSAGE =  """COMMANDS LIST
====================
All special commands start with '/'
----
>>> /help: show this help message
----
>>> <tab>:  autocomplete.
----
>>> /docs: print out documentation for DSL data objects.
>>> /gbq tables [keyword]: list tables in tabular format (searches table name only; if 1 found, shows fields).
>>> /gbq fields [table]: list all fields in a specific table.
>>> /gbq fields "search": search for fields containing string across all tables.
>>> /gbq fields [table] "search": search for fields containing string within a specific table.
>>> /gbq query [table]: generate SQL query templates for a table (ready to copy-paste).
>>> /gbq fieldquery [table] [field]: generate field-specific SQL templates (handles nested/repeated fields).
>>> /export_as_json: save results from last query as JSON file.
>>> /export_as_csv: save results from last query as CSV file.
>>> /export_as_gist: save results from last query as Github GIST.
>>> /export_as_html: save results from last query as HTML file.
>>> /export_as_bar_chart: save results from last query as Plotly bar chart.
>>> /export_as_jupyter: save results from last query as Jupyter notebook.
>>> /export_as_gsheets: save results from last query as Google Sheets (requires gspread credentials).
>>> /show [optional: N]: print N results from last query, trying to build URLs for objects. Default N=10.
>>> /json_compact: print results of last query as single-line JSON.
>>> /json_full: print results of last query as formatted JSON.
>>> /url: resolve a Dimensions ID into a public URL.
----
>>> <Ctrl-o>: search docs online (type a search query first).
>>> <Ctrl-c>: abort query.
>>> <Ctrl-d>: exit console.
----
>>> /quit: exit console
====================
*ABOUT AUTOCOMPLETE*
Including a space between query elements (= keywords and operators) leads to better autocomplete results."""

WELCOME_MESSAGE = "Welcome! Type /help for more info."
# WELCOME_MESSAGE = "Welcome! Type help for more info. Ready to query endpoint: %s"



#
#
# DIMENSIONS QUERY AND DATA HANDLING
#
#


class DslResultsBuffer(object):
    current_json = ""
    current_query = ""

    def save(self, json_data, query):
        self.current_json = json_data
        self.current_query = query
        self.is_recording = False

    def retrieve(self):
        return (self.current_json, self.current_query)



class CommandsManager(object):

    def __init__(self, dslclient, databuffer):
        self.dsl = dslclient
        self.bf = databuffer

    def handle(self, text):
        "process text and delegate"
        if text.replace("\n", "").strip().startswith("/show") or text.replace("\n", "").strip().startswith("/json"):
            self.show(text.replace("\n", "").strip())

        elif text.replace("\n", "").strip().startswith("/export"):
            self.export(text.replace("\n", "").strip())

        elif text.replace("\n", "").strip().startswith("/docs"):
            self.docs_full(text.replace("\n", "").strip())

        elif text.replace("\n", "").strip().startswith("/gbq"):
            self.gbq_handler(text.replace("\n", "").strip())

        elif text.replace("\n", "").strip().startswith("/url"):
            self.url_resolver(text.replace("\n", "").strip())

        else:
            return self.query(text)


    def url_resolver(self, text):
        """
        turn an ID into a Dimensions URL - print out results
        """
        text = text.replace("/url", "").strip()
        if len(text) > 0:
            print_dimensions_url(text)

    def query(self, text):
        """main procedure after user query dsl"""
        # lazy complete
        text = line_add_lazy_return(text)
        text = line_add_lazy_describe(text)
        click.secho("You said: %s" % text, fg="black", dim=True)
        # RUN QUERY
        res = self.dsl.query(text)
        # errors info gets printed out by the API by default
        if not "errors" in res.json.keys():
            if "_warnings" in res.json.keys():
                click.secho("WARNINGS [{}]".format(len(res.json["_warnings"])), fg="red")
                # print("WARNINGS [{}]".format(len(res.json["_warnings"])))
                print("\n".join([s for s in res.json["_warnings"]]))
                click.secho("---", dim=True)
            # search query
            if text.strip().startswith("search"):
                print_json_stats(res, text)
                if self.bf: self.bf.save(res.json, text)
                if True:
                    click.secho("---", dim=True)
                    preview_results(res.json, maxitems=5)
                return res  # 2019-03-31
            # describe queries and other functions: just show the data
            else:
                if self.bf: self.bf.save(res.json, text)
                click.secho("---", dim=True)
                print_json_full(res.json)


    def docs_full(self, text):
        """
        print out docs infos from 'describe' API
        """
        text = text.replace("/docs", "").split()
        if len(text) > 0:
            if text[0] in G.entities():
                res = self.dsl.query(f"describe entity {text[0]}")
            else:
                res = self.dsl.query(f"describe source {text[0]}")
            if "errors" in res.json.keys():
                print(res.json["errors"])
                return 
            # show all fields 
            click.secho("=====\nFIELDS")
            for x in sorted(res.json['fields']):
                d = res.json['fields'][x].get('description') or  ""
                typ = res.json['fields'][x].get('type', "")
                ise = res.json['fields'][x].get('is_entity', "")
                isfa = res.json['fields'][x].get('is_facet', "")
                isfi = res.json['fields'][x].get('is_filter', "")
                if isfa:
                    infos = f"[type={typ}, filter={isfi}, facet={isfa}]"
                else:
                    infos = f"[type={typ}, filter={isfi}]"
                click.echo(click.style(x, bold=True) + " " + click.style(infos, dim=True) + \
                    " " + click.style(d))
            if 'metrics' in res.json:
                click.secho("=====\nMETRICS")
                for x in res.json['metrics']:
                    d = res.json['metrics'][x]['description'] or "no description"
                    click.echo(click.style(x, bold=True) + " " + click.style(d, dim=True))
            if 'fieldsets' in res.json:
                click.secho("=====\nFIELDSETS")
                f = res.json['fieldsets']
                if f:
                    click.secho(", ".join([x for x in f]), bold=True)
            if 'search_fields' in res.json:
                click.secho("=====\nSEARCH FIELDS")
                f = res.json['search_fields']
                if f:
                    click.secho(", ".join([x for x in f]), bold=True)

        else:
            print("Please specify a source or entity.")


    def export(self, text):
        """
        save results of a query to a file
        """
        init_exports_folder(USER_EXPORTS_DIR)
        if self.bf: 
            jsondata, query = self.bf.retrieve()
        else:
            jsondata, query = None, None
        if not jsondata:
            print("Nothing to export - please run a search first.")
            return
        CONNECTION = get_global_connection()
        api_endpoint = CONNECTION.url
        # cases
        if text == "/export_as_html":
            export_json_html(jsondata, query, api_endpoint, USER_EXPORTS_DIR)

        elif text == "/export_as_gist":
            export_gist(jsondata, query, api_endpoint)

        elif text == "/export_as_csv":
            export_json_csv(jsondata, query, USER_EXPORTS_DIR)

        elif text == "/export_as_json":
            export_json_json(jsondata, query, USER_EXPORTS_DIR)

        elif text == "/export_as_bar_chart":
            export_as_bar_chart(jsondata, query, USER_EXPORTS_DIR)

        elif text == "/export_as_jupyter":
            export_as_jupyter(jsondata, query, USER_EXPORTS_DIR)

        elif text == "/export_as_gsheets":
            export_as_gsheets_wrapper(jsondata, query)


    def show(self, text):
        """
        show results of a query
        """
        DEFAULT_NO_RECORDS = 10
        # text = text.replace(".show", "").strip()
        text = text.strip()

        if self.bf: 
            jsondata, query = self.bf.retrieve()
        else:
            jsondata, query = None, None
        if not jsondata:
            print("Nothing to show - please run a search first.")
            return
        # cases
        if text == "/json_compact":
            print_json_compact(jsondata)
        elif text == "/json_full":
            print_json_full(jsondata)
        else:
            # must be a simple "/show" + X command
            try:
                no = text.replace("/show", "").strip()
                slice_no = int(no)
            except ValueError:
                slice_no = DEFAULT_NO_RECORDS
            preview_results(jsondata, maxitems=slice_no)


    def gbq_handler(self, text):
        """
        Handle /gbq command with sub-commands for BigQuery schema exploration
        """
        try:
            from ..utils.gbq_utils import (
                get_gbq_client, list_tables, list_fields,
                print_tables, print_fields, print_query_template,
                print_field_query_template
            )
        except ImportError as e:
            click.secho("BigQuery integration not available.", fg="red")
            click.secho("Install with: pip install google-cloud-bigquery", dim=True)
            return

        # Parse: /gbq tables [search_term]
        #        /gbq fields [table_name]
        #        /gbq fields "search_term"
        #        /gbq fields [table_name] "search_term"
        #        /gbq query [table_name]
        #        /gbq fieldquery [table_name] [field_name]

        parts = text.replace("/gbq", "").strip().split()

        if len(parts) == 0:
            click.secho("Usage:", bold=True)
            click.secho("  /gbq tables [keyword]            - list tables (searches table name only; if 1 found, shows fields)", dim=True)
            click.secho("  /gbq fields [table]              - list all fields in a table", dim=True)
            click.secho("  /gbq fields \"search\"              - search for fields containing string across all tables", dim=True)
            click.secho("  /gbq fields [table] \"search\"      - search for fields within a specific table", dim=True)
            click.secho("  /gbq query [table]               - generate SQL query templates for a table", dim=True)
            click.secho("  /gbq fieldquery [table] [field]  - generate field-specific SQL templates (handles nested/array fields)", dim=True)
            click.secho("\nDefault dataset: dimensions-ai.data_analytics", dim=True)
            return

        subcommand = parts[0]

        try:
            client = get_gbq_client()

            if subcommand == "tables":
                search_term = parts[1] if len(parts) > 1 else None
                tables = list_tables(client, search_term=search_term)
                print_tables(tables)

                # If exactly one table found, also display its fields
                if len(tables) == 1:
                    click.echo()  # Add spacing
                    table_name = tables[0]['name']
                    click.secho(f"Showing fields for table: {table_name}", fg="green", bold=True)
                    fields = list_fields(client, table_name=table_name)
                    print_fields(fields)

            elif subcommand == "fields":
                if len(parts) == 1:
                    # /gbq fields - show all fields across all tables
                    fields = list_fields(client)
                    print_fields(fields)
                elif len(parts) == 2:
                    arg = parts[1]
                    # Check if argument is quoted (search term) or not (table name)
                    if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                        # /gbq fields "search" - search for fields containing the term across all tables
                        search_term = arg[1:-1]  # Remove quotes
                        fields = list_fields(client, search_term=search_term)
                        print_fields(fields, search_term=search_term)
                    else:
                        # /gbq fields <table> - show fields for specific table
                        fields = list_fields(client, table_name=arg)
                        print_fields(fields)
                elif len(parts) == 3:
                    # /gbq fields <table> "search" - search within specific table
                    table_name = parts[1]
                    search_arg = parts[2]
                    if (search_arg.startswith('"') and search_arg.endswith('"')) or (search_arg.startswith("'") and search_arg.endswith("'")):
                        search_term = search_arg[1:-1]  # Remove quotes
                        fields = list_fields(client, table_name=table_name, search_term=search_term)
                        print_fields(fields, search_term=search_term)
                    else:
                        click.secho("Error: Second argument must be quoted for search", fg="red")
                        click.secho("Usage: /gbq fields <table> \"search\"", dim=True)
                else:
                    click.secho("Error: Too many arguments", fg="red")
                    click.secho("Usage: /gbq fields [table] OR /gbq fields \"search\" OR /gbq fields <table> \"search\"", dim=True)

            elif subcommand == "query":
                if len(parts) == 2:
                    # /gbq query <table> - generate SQL query templates
                    table_name = parts[1]
                    print_query_template(table_name)
                else:
                    click.secho("Error: Please specify a table name", fg="red")
                    click.secho("Usage: /gbq query <table_name>", dim=True)

            elif subcommand == "fieldquery":
                if len(parts) == 3:
                    # /gbq fieldquery <table> <field> - generate field-specific SQL query templates
                    table_name = parts[1]
                    field_name = parts[2]
                    client = get_gbq_client()
                    print_field_query_template(client, table_name, field_name)
                else:
                    click.secho("Error: Please specify table and field names", fg="red")
                    click.secho("Usage: /gbq fieldquery <table_name> <field_name>", dim=True)

            else:
                click.secho(f"Unknown sub-command: {subcommand}", fg="red")
                click.secho("Available sub-commands: tables, fields, query, fieldquery", dim=True)

        except Exception as e:
            click.secho(f"BigQuery error: {str(e)}", fg="red")
            if "credentials" in str(e).lower() or "authentication" in str(e).lower():
                click.secho("Tip: Set GOOGLE_APPLICATION_CREDENTIALS or run 'gcloud auth application-default login'", dim=True)




#
#
# MAIN CLI
#
#


def run(instance="live"):
    """
    run the repl
    """

    try:
        do_global_login(instance=instance)
        CLIENT = Dsl(verbose=False)
    except requests.exceptions.HTTPError as err:
        click.secho(err)
        sys.exit(1)

    # dynamically retrieve dsl version 
    click.secho(WELCOME_MESSAGE)
    try:
        _info = CLIENT.query("describe version")['release']
    except:
        _info = "not available"
    click.secho(f"Using endpoint: {CLIENT._url} - DSL version: {_info}", dim=True)

    # history
    session = PromptSession(history=SelectiveFileHistory(USER_HISTORY_FILE))  ### December 30, 2024 
    # session = PromptSession()

    databuffer = DslResultsBuffer()

    # REPL loop
    while True:
        try:
            text = session.prompt(
                "\n> ",
                default="",  # you can pass a default text to begin with
                completer=CleverCompleter(),
                complete_style=CompleteStyle.MULTI_COLUMN,
                # validator=BasicValidator(),
                # validate_while_typing=False,
                multiline=False,
                complete_while_typing=True,
                lexer=BasicLexer(),
                key_bindings=bindings,
            )
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.
        except Exception as e:
            print(e)
            sys.exit(0)  
        else:
            if text.strip() == "":
                continue
            elif text == "/quit":
                break
            elif text == "/help":
                click.secho(HELP_MESSAGE, dim=True)
                continue
            # cm = CommandsManager(CLIENT,databuffer)
            # cm.handle(text)
            try:
                cm = CommandsManager(CLIENT,databuffer)
                cm.handle(text)
            except Exception as e:
                print(e)
                continue
    print("GoodBye!")


if __name__ == "__main__":
    run()
