#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import click
from pprint import pprint
import webbrowser

from .VERSION import *

from .core.auth import (USER_DIR, USER_CONFIG_FILE_PATH, USER_HISTORY_FILE,
                        do_global_login, get_global_connection,
                        save_cli_session, load_cli_session)
from .core.api import *
from .utils.misc_utils import open_multi_platform
from .utils.repl_utils import init_config_folder, print_warning_prompt_version, preview_contents
from .utils.dim_utils import dimensions_url
from .utils.version_utils import print_dimcli_report, is_dimcli_outdated

try:
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import CompleteStyle
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style
    PROMPT_TOOLKIT_VERSION_OK = True
except:
    PROMPT_TOOLKIT_VERSION_OK = False # => repl disabled


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("instance_name", nargs=1, default="live")
@click.option(
    "--init",
    is_flag=True,
    help="Create a local API configuration.")
@click.option(
    "--settings",
    is_flag=True,
    help="Show the local configuration.")
@click.option(
    "--checkversion",
    is_flag=True,
    help="Check if dimcli is up to date.")
@click.option(
    "--history", is_flag=True, help="Open query history file.")
@click.option(
    "--identifier", "-i", help="Open Dimensions webapp from an object ID.")

@click.option(
    "--query", "-q", help="Run a DSL query and print results to stdout.")
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["json", "csv", "df"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format for -q results.")
@click.option(
    "--nice", "nice_flag", is_flag=True,
    help="Flatten nested structures into readable strings (applies to csv/df formats).")
@click.option(
    "--html", "html_flag", is_flag=True,
    help="Add Dimensions hyperlinks (applies to df format only; outputs HTML).")
@click.pass_context
def main_cli(ctx, instance_name=None, init=False, settings=False, checkversion=False, history=False, identifier=None, query=None, output_format="json", nice_flag=False, html_flag=False):
    """
    Python client for the Dimensions Analytics API.
    More info: https://github.com/digital-science/dimcli
    """
    if not (identifier or query):
        click.secho("Dimcli - Dimensions API Client (" + VERSION + ")", dim=True)

    if init:
        init_config_folder(USER_DIR, USER_CONFIG_FILE_PATH)
        return

    if checkversion:
        print_dimcli_report()
        return

    if identifier:
        url = dimensions_url(identifier)
        if not url: 
            click.secho("Cannot resolve automatically. Can be a patent, dataset or clinical trial ID. Falling back to search ..")
            url = dimensions_search_url(identifier)
        else:
            click.secho("Got a match: " + url)
        webbrowser.open(url)
        return 


    if query:
        import json as _json
        session = load_cli_session()
        if session:
            import dimcli.core.auth as _auth
            _auth.CONNECTION = session
            click.secho("Reusing cached session.", dim=True, err=True)
        else:
            if not os.path.exists(USER_CONFIG_FILE_PATH):
                click.secho(
                    "Credentials file not found - you can create one by typing: `dimcli --init`",
                    fg="red",
                )
                return
            click.secho("Authenticating...", dim=True, err=True)
            do_global_login(instance=instance_name)
            session = get_global_connection()
            save_cli_session(session)
        dsl = Dsl(verbose=False)
        result = dsl.query(query)
        if output_format == "json":
            click.echo(_json.dumps(result.json, indent=2))
        else:
            df = result.as_dataframe()
            if df is None:
                click.secho("Error: could not convert results to a dataframe.", fg="red", err=True)
                return
            # --nice and/or --html require knowing the source type
            if nice_flag or html_flag:
                from .utils.repl_utils import line_search_subject
                source = line_search_subject(query)
            # --nice: flatten nested structures using source-specific converters
            if nice_flag:
                from .utils.converters import (DslPubsConverter, DslGrantsConverter,
                    DslPatentsConverter, DslPolicyDocumentsConverter,
                    DslClinicaltrialsConverter, DslDatasetsConverter,
                    DslReportsConverter, DslSourceTitlesConverter,
                    DslOrganizationsConverter, DslResearchersConverter)
                _converters = {
                    "publications": DslPubsConverter,
                    "grants": DslGrantsConverter,
                    "patents": DslPatentsConverter,
                    "policy_documents": DslPolicyDocumentsConverter,
                    "clinical_trials": DslClinicaltrialsConverter,
                    "datasets": DslDatasetsConverter,
                    "reports": DslReportsConverter,
                    "source_titles": DslSourceTitlesConverter,
                    "organizations": DslOrganizationsConverter,
                    "researchers": DslResearchersConverter,
                }
                if source in _converters:
                    df = _converters[source](df).run()
            # --html: add Dimensions hyperlinks (df format only, outputs HTML)
            if html_flag:
                if output_format != "df":
                    click.secho("Note: --html is only supported with --format df; ignoring.", dim=True, err=True)
                else:
                    from .utils.dim_utils import dimensions_styler
                    df = dimensions_styler(df, source)
                    click.echo(df.to_html())
                    return
            if output_format == "csv":
                click.echo(df.to_csv(index=False))
            else:  # df
                try:
                    click.echo(df.to_markdown(index=False, tablefmt="grid"))
                except ImportError:
                    click.echo(df.to_string(index=False))
        return

    if not os.path.exists(USER_CONFIG_FILE_PATH):
        click.secho(
            "Credentials file not found - you can create one by typing: `dimcli --init`",
            fg="red",
        )
        click.secho(
            "More info: https://github.com/digital-science/dimcli#credentials-file",
            dim=True,
        )
        return

    if settings:
        preview_contents(USER_CONFIG_FILE_PATH)
        return

    if history:
        if os.path.exists(USER_HISTORY_FILE):
            open_multi_platform(USER_HISTORY_FILE)
        return

    if PROMPT_TOOLKIT_VERSION_OK:
        from .repl import repl
        # try online version check
        test = is_dimcli_outdated()
        if test:
            click.secho("====")
            click.secho("Heads up: there is a newer version of Dimcli available.", bold=True)
            click.secho("Update with `pip install dimcli -U` or, for more info, visit https://pypi.org/project/dimcli .\n====")
        # launch REPL
        repl.run(instance_name)
    else:
        print_warning_prompt_version()



if __name__ == "__main__":
    main_cli()
