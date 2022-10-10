import sys
import click
from pluggy import PluginManager, HookimplMarker

hookimpl = HookimplMarker("data_pipelines_cli")


@hookimpl
def setup_project(config, args):
    """This hook is used to process the initial config
    and possibly input arguments.
    """
    if args:
        config.process_args(args)

    return config


pm = PluginManager("data_pipelines_cli")

# load all hookimpls from the local module's namespace
plugin_name = pm.register(sys.modules[__name__])

