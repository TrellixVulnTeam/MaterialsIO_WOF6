"""Utilities for working with parsers from other applications"""

from stevedore.extension import ExtensionManager
from stevedore.driver import DriverManager
from typing import Iterator, Union, Dict
from collections import namedtuple

from materials_io.adapters.base import BaseAdapter
from materials_io.base import BaseParser

ParseResult = namedtuple('ParseResult', ['group', 'parser', 'metadata'])


def _output_plugin_info(mgr: ExtensionManager) -> dict:
    """Gets information about all plugins attached to a particular manager

    Args:
        mgr (ExtensionManager): Plugin manager
    Returns:
        (dict): Dictionary where keys are plugin ids and values are descriptions
    """

    output = {}
    for name, ext in mgr.items():
        plugin = ext.plugin()
        output[name] = {
            'description': plugin.__doc__.split("\n")[0],
        }
        if hasattr(plugin, 'version'):
            output[name]['version'] = plugin.version()
    return output


def get_available_parsers():
    """Get information about the available parsers

    Returns:
        [dict]: Descriptions of available parsers
    """
    mgr = ExtensionManager(
        namespace='materialsio.parser',
    )

    # Get information about each parser
    return _output_plugin_info(mgr)


def get_available_adapters() -> dict:
    """Get information on all available adapters

    Returns:
        (dict) Where keys are adapter names and values are descriptions
    """

    return _output_plugin_info(ExtensionManager(namespace='materialsio.adapter'))


def get_parser(name: str) -> BaseParser:
    """Load a parser object

    Args:
        name (str): Name of parser
    Returns:
        (BaseParser) Requested parser
    """
    return DriverManager(
        namespace='materialsio.parser',
        name=name,
        invoke_on_load=True
    ).driver


def get_adapter(name: str) -> BaseAdapter:
    """Load an adapter

    Args:
        name (str): Name of adapter
    Returns:
        (BaseAdapter) Requested adapter
    """

    # Load the adapter
    mgr = DriverManager(
        namespace='materialsio.adapter',
        name=name,
        invoke_on_load=True
    )

    # Give it to the user
    return mgr.driver


def execute_parser(name, group, context=None, adapter=None):
    """Invoke a parser on a certain group of data

    Args:
        name (str): Name of the parser
        group ([str]): Paths to group of files to be parsed
        context (dict): Context of the files
        adapter (str): Name of adapter to use to transform metadata
    Returns:
        ([dict]): Metadata generated by the parser
    """
    metadata = get_parser(name).parse(group, context)
    if adapter is not None:
        adapter = get_adapter(adapter)
        return adapter.transform(metadata)
    return metadata


def run_all_parsers(directory: str, context=None,
                    adapter_map: Union[None, str, Dict[str, str]] = None,
                    default_adapter: Union[None, str] = None) -> Iterator[ParseResult]:
    """Run all known files on a directory of files

    Args:
        directory (str): Path to directory to be parsed
        context (dict): Context of the files
        adapter_map (str, dict): Map of parser name to the desired adapter.
            Use 'match' to find adapters with the same names
        default_adapter (str): Adapter to use if no other adapter is defined
    Yields
        ((str), str, dict) Tuple of (1) group of files, (2) name of parser, (3) metadata
    """

    # Get the list of parsers
    parsers = get_available_parsers()

    # Make the adapter map
    if adapter_map is None:
        adapter_map = {}
    elif adapter_map == 'match':
        adapters = get_available_adapters()
        adapter_map = dict((x, x) for x in parsers if x in adapters)

    # Get the list of known parsers
    for name in parsers:
        # Get the parser and adapter
        parser = get_parser(name)
        adapter = adapter_map.get(name, default_adapter)
        if adapter is not None:
            adapter = get_adapter(adapter)

        for group, metadata in parser.parse_directory(directory, context):
            # Run the adapter, if defined
            if adapter is not None:
                try:
                    metadata = adapter.transform(metadata)
                except Exception:
                    continue
                if metadata is None:
                    continue

            yield ParseResult(group, name, metadata)
