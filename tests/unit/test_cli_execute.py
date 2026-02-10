"""
Unit tests for CLI execute subcommand integration
"""

import pytest
from netwalker.cli import create_parser, parse_args


class TestExecuteSubcommand:
    """Test the execute subcommand CLI integration"""

    def test_execute_subcommand_exists(self):
        """Test that execute subcommand is registered"""
        parser = create_parser()
        # Note: args.command is the subcommand name from subparsers
        # The --command argument value is stored in a different attribute
        args = parse_args(['execute', '--filter', '*-uw*', '--command', 'show version'])
        # Verify the subcommand was parsed (command attribute exists)
        assert hasattr(args, 'filter')
        assert hasattr(args, 'command')
        assert args.filter == '*-uw*'

    def test_execute_required_filter_argument(self):
        """Test that --filter argument is required"""
        with pytest.raises(SystemExit):
            parse_args(['execute', '--command', 'show version'])

    def test_execute_required_command_argument(self):
        """Test that --command argument is required"""
        with pytest.raises(SystemExit):
            parse_args(['execute', '--filter', '*-uw*'])

    def test_execute_filter_argument_short_form(self):
        """Test that -f short form works for filter"""
        args = parse_args(['execute', '-f', '*-uw*', '--command', 'show version'])
        assert args.filter == '*-uw*'

    def test_execute_filter_argument_long_form(self):
        """Test that --filter long form works"""
        args = parse_args(['execute', '--filter', 'BORO-*', '--command', 'show version'])
        assert args.filter == 'BORO-*'

    def test_execute_command_argument_short_form(self):
        """Test that -cmd short form works for command"""
        args = parse_args(['execute', '--filter', '*', '-cmd', 'show ip route'])
        # The --command argument value is stored in args.command (overrides subparser command)
        assert args.command == 'show ip route'

    def test_execute_command_argument_long_form(self):
        """Test that --command long form works"""
        args = parse_args(['execute', '--filter', '*', '--command', 'show version'])
        assert args.command == 'show version'

    def test_execute_config_default_value(self):
        """Test that config defaults to netwalker.ini"""
        args = parse_args(['execute', '--filter', '*', '--command', 'show version'])
        assert args.config == 'netwalker.ini'

    def test_execute_config_custom_value(self):
        """Test that config can be customized"""
        args = parse_args(['execute', '--filter', '*', '--command', 'show version',
                          '--config', 'custom.ini'])
        assert args.config == 'custom.ini'

    def test_execute_config_short_form(self):
        """Test that -c short form works for config"""
        args = parse_args(['execute', '-f', '*', '-cmd', 'show version', '-c', 'test.ini'])
        assert args.config == 'test.ini'

    def test_execute_output_default_value(self):
        """Test that output defaults to current directory"""
        args = parse_args(['execute', '--filter', '*', '--command', 'show version'])
        assert args.output == '.'

    def test_execute_output_custom_value(self):
        """Test that output can be customized"""
        args = parse_args(['execute', '--filter', '*', '--command', 'show version',
                          '--output', './reports'])
        assert args.output == './reports'

    def test_execute_output_short_form(self):
        """Test that -o short form works for output"""
        args = parse_args(['execute', '-f', '*', '-cmd', 'show version', '-o', './output'])
        assert args.output == './output'

    def test_execute_all_arguments_combined(self):
        """Test all arguments together"""
        args = parse_args([
            'execute',
            '--config', 'test.ini',
            '--filter', '*-uw*',
            '--command', 'show ip eigrp vrf WAN neigh',
            '--output', './results'
        ])
        # Note: args.command contains the --command argument value (not 'execute')
        assert args.config == 'test.ini'
        assert args.filter == '*-uw*'
        assert args.command == 'show ip eigrp vrf WAN neigh'
        assert args.output == './results'

    def test_execute_all_arguments_short_form(self):
        """Test all arguments with short forms"""
        args = parse_args([
            'execute',
            '-c', 'test.ini',
            '-f', 'BORO-*',
            '-cmd', 'show version',
            '-o', './out'
        ])
        assert args.config == 'test.ini'
        assert args.filter == 'BORO-*'
        assert args.command == 'show version'
        assert args.output == './out'

    def test_execute_filter_with_sql_wildcards(self):
        """Test filter patterns with SQL wildcards"""
        # Test % wildcard
        args = parse_args(['execute', '-f', '%uw%', '-cmd', 'show version'])
        assert args.filter == '%uw%'

        # Test _ wildcard
        args = parse_args(['execute', '-f', 'BORO-SW-UW0_', '-cmd', 'show version'])
        assert args.filter == 'BORO-SW-UW0_'

        # Test combined wildcards
        args = parse_args(['execute', '-f', '%SW_UW%', '-cmd', 'show version'])
        assert args.filter == '%SW_UW%'

    def test_execute_complex_command_string(self):
        """Test complex command strings with spaces and special characters"""
        complex_cmd = 'show ip eigrp vrf WAN neighbors detail'
        args = parse_args(['execute', '-f', '*', '-cmd', complex_cmd])
        assert args.command == complex_cmd

    def test_execute_command_with_quotes(self):
        """Test command strings that might contain quotes"""
        cmd_with_quotes = "show running-config | include 'interface'"
        args = parse_args(['execute', '-f', '*', '-cmd', cmd_with_quotes])
        assert args.command == cmd_with_quotes
