# !/usr/bin/env python
#  -*- coding: UTF-8 -*-
"""
Unit tests for the Dimcli CLI -q option

python -m dimcli.tests.test_cli

"""

from __future__ import print_function

import unittest, json, click
from click.testing import CliRunner

from ..main_cli import main_cli
from .settings import API_INSTANCE


class TestCli(unittest.TestCase):

    """
    Tests for the -q / --query CLI option and related flags.
    Requires a valid API credentials file (~/.dimensions/dsl.ini).
    """

    click.secho("**test_cli.py**", fg="red")

    def setUp(self):
        self.runner = CliRunner(mix_stderr=False)
        self.query = 'search publications for "malaria" return publications[id+title+year] limit 3'

    def test_001(self):
        click.secho("\nTEST 001: -q returns valid JSON by default.", bg="green")
        result = self.runner.invoke(main_cli, ["-q", self.query])
        print(" ==> exit_code:", result.exit_code)
        if result.exception:
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("publications", data)
        print(" ==> publications returned:", len(data["publications"]))
        click.secho("Completed test successfully", fg="green")

    def test_002(self):
        click.secho("\nTEST 002: -q -f csv returns CSV output.", bg="green")
        result = self.runner.invoke(main_cli, ["-q", self.query, "-f", "csv"])
        print(" ==> exit_code:", result.exit_code)
        self.assertEqual(result.exit_code, 0)
        lines = result.output.strip().splitlines()
        self.assertGreater(len(lines), 1)  # at least header + one row
        self.assertIn("id", lines[0])
        print(" ==> CSV rows (incl. header):", len(lines))
        click.secho("Completed test successfully", fg="green")

    def test_003(self):
        click.secho("\nTEST 003: -q -f df returns a formatted table.", bg="green")
        result = self.runner.invoke(main_cli, ["-q", self.query, "-f", "df"])
        print(" ==> exit_code:", result.exit_code)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("id", result.output)
        print(" ==> output preview:\n", result.output[:300])
        click.secho("Completed test successfully", fg="green")

    def test_004(self):
        click.secho("\nTEST 004: -q -f df --nice returns a flattened table.", bg="green")
        result = self.runner.invoke(main_cli, ["-q", self.query, "-f", "df", "--nice"])
        print(" ==> exit_code:", result.exit_code)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("id", result.output)
        print(" ==> output preview:\n", result.output[:300])
        click.secho("Completed test successfully", fg="green")

    def test_005(self):
        click.secho("\nTEST 005: -q -f df --html returns an HTML table.", bg="green")
        result = self.runner.invoke(main_cli, ["-q", self.query, "-f", "df", "--html"])
        print(" ==> exit_code:", result.exit_code)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("<table", result.output)
        self.assertIn("<th", result.output)
        print(" ==> HTML output length:", len(result.output))
        click.secho("Completed test successfully", fg="green")

    def test_006(self):
        click.secho("\nTEST 006: --html without -f df is ignored (falls back to df table).", bg="green")
        result = self.runner.invoke(main_cli, ["-q", self.query, "-f", "csv", "--html"])
        print(" ==> exit_code:", result.exit_code)
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("<table", result.output)  # HTML should not appear for csv
        click.secho("Completed test successfully", fg="green")


if __name__ == "__main__":
    unittest.main()
