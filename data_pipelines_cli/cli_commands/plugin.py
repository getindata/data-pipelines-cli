import sys
from pluggy import PluginManager, HookimplMarker, HookspecMarker

CLI_HOOK_NAMESPACE = "data_pipelines_cli"

hookspec = HookspecMarker(CLI_HOOK_NAMESPACE)
hookimpl = HookimplMarker(CLI_HOOK_NAMESPACE)


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
