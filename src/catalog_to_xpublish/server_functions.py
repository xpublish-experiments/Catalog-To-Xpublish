import dataclasses
import warnings
import xpublish
# NOTE: we are using a local version of xpublish (release is missing features we need)
from fastapi import FastAPI
from xpublish_opendap_server.base import (
    CatalogEndpoint,
)
from xpublish_opendap_server.provider_plugin import (
    DatasetProviderPlugin,
)
from xpublish_opendap_server.factory import (
    CatalogImplementation,
    CatalogImplementationFactory,
)
from pathlib import Path
from typing import (
    List,
    Optional,
)


@dataclasses.dataclass
class AppComponents:
    """A class to hold the different inputs for launching our server app."""
    catalog_path: Path
    catalog_name: str
    catalog_implementation: CatalogImplementation
    name: str
    xpublish_plugins: list


def validate_arguments(
    catalog_path: Path,
    catalog_type: str,
    app_name: Optional[str] = None,
    xpublish_plugins: Optional[List[xpublish.Plugin]] = None,
) -> AppComponents:
    """Validates the arguments passed to the create_app function."""
    # check catalog path argument and get name
    if not isinstance(catalog_path, Path):
        raise TypeError(
            f'catalog_path must be a Path object, not {type(catalog_path)}'
        )
    if not catalog_path.exists():
        raise FileNotFoundError(
            f'catalog_path={catalog_path} does not exist.'
        )

    catalog_name: str = catalog_path.name.replace(catalog_path.suffix, '')

    # check catalog type argument
    if not isinstance(catalog_type, str):
        raise TypeError(
            f'catalog_type must be a str, not {type(catalog_type)}'
        )
    catalog_type = catalog_type.lower()
    catalog_implementations = CatalogImplementationFactory.get_all_implementations()
    if not catalog_type in catalog_implementations.keys():
        raise KeyError(
            f'catalog_type={catalog_type} is not in {catalog_implementations.keys()}.'
        )
    catalog_implementation = catalog_implementations[catalog_type]

    # check app name argument
    if not app_name:
        app_name = 'Catalog_Xpublish_Server'
    elif not isinstance(app_name, str):
        raise TypeError(
            f'app_name must be a str, not {type(app_name)}'
        )

    # check plugins list argument
    if not xpublish_plugins:
        xpublish_plugins = []
    if not isinstance(xpublish_plugins, list):
        raise TypeError(
            f'xpublish_plugins must be a list of xpublish.Plugin objects, not {type(xpublish_plugins)}'
        )

    return AppComponents(
        catalog_path=catalog_path,
        catalog_name=catalog_name,
        catalog_implementation=catalog_implementation,
        name=app_name,
        xpublish_plugins=xpublish_plugins,
    )


def create_app(
    catalog_path: Path,
    catalog_type: str,
    app_name: Optional[str] = None,
    xpublish_plugins: Optional[List[xpublish.Plugin]] = None,
) -> FastAPI:
    """Main function to create the server app.

    Args:
        catalog_path: The path to the catalog file (i.e., yaml or json).
        catalog_type: The type of catalog to parse.
        app_name: The name of the app.
        xpublish_plugins: A list of external xpublish plugin classes to use.
    Returns:
        A FastAPI app object.
    ."""
    # 0. validate input arguments
    app_inputs: AppComponents = validate_arguments(
        catalog_path=catalog_path,
        catalog_type=catalog_type,
        app_name=app_name,
        xpublish_plugins=xpublish_plugins,
    )

    # 1. parse catalog using appropriate catalog search method
    catalog_searcher = app_inputs.catalog_implementation.catalog_search(
        catalog_path=catalog_path,
    )
    catalog_endpoints: List[CatalogEndpoint] = catalog_searcher.parse_catalog()

    # 2. Start a Xpublish server
    app = FastAPI(
        title=f'{app_inputs.name}: {app_inputs.catalog_name}'
    )

    # 2. Iterate through the endpoints and add them to the server
    for cat_end in catalog_endpoints:
        cat_prefix = cat_end.catalog_path
        if cat_prefix == '/':
            cat_prefix = ''

        # 2.1 if the endpoint has data, mount a Xpublish server
        if cat_end.contains_datasets:
            rest_server = xpublish.Rest()
            rest_server.init_app_kwargs(
                app_kws={
                    'title': app_inputs.catalog_name + cat_prefix,
                },
            )

            # add dataset provider plugin
            provider_plugin = DatasetProviderPlugin(
                catalog_endpoint=cat_end,
                io_class=app_inputs.catalog_implementation.catalog_to_xarray,
            )
            rest_server.register_plugin(
                plugin=provider_plugin,
                plugin_name=cat_prefix,
            )
            assert cat_prefix in rest_server.plugins

            # add all non-dataset provider plugins
            try:
                for plugin in app_inputs.xpublish_plugins:
                    assert issubclass(plugin, xpublish.Plugin)
                    plugin = plugin()
                    rest_server.register_plugin(
                        plugin=plugin,
                    )
                    assert plugin.name in rest_server.plugins
            except AssertionError:
                warnings.warn(
                    f'Could not add plugin={plugin} to the Xpublish server.'
                )
                continue

            # add the base router (for some reason this needs to come after)
            router = app_inputs.catalog_implementation.catalog_router(
                catalog_endpoint_obj=cat_end,
                prefix='',
            )
            rest_server.app.include_router(router=router.router)

            # mount to the main application
            app.mount(
                path=cat_prefix,
                app=rest_server.app,
            )

        # 2.2 if the endpoint has no data, add a router to the main application
        else:
            # make a router for each endpoint
            router = app_inputs.catalog_implementation.catalog_router(
                catalog_endpoint_obj=cat_end,
            )
            app.include_router(router=router.router)
    return app
