import logging
import dataclasses
import xpublish
from fastapi import FastAPI
from catalog_to_xpublish.base import (
    CatalogEndpoint,
)
from catalog_to_xpublish.log import (
    LoggingConfigDict,
    APILogging,
)
from catalog_to_xpublish.provider_plugin import (
    DatasetProviderPlugin,
)
from catalog_to_xpublish.factory import (
    CatalogImplementation,
    CatalogImplementationFactory,
)
from pathlib import Path
from typing import (
    List,
    Optional,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class AppComponents:
    """A class to hold the different inputs for launching our server app."""
    catalog_path: Path | str
    catalog_name: str
    catalog_implementation: CatalogImplementation
    name: str
    xpublish_plugins: list


def validate_arguments(
    catalog_path: Path | str,
    catalog_type: str,
    app_name: Optional[str] = None,
    xpublish_plugins: Optional[List[xpublish.Plugin]] = None,
) -> AppComponents:
    """Validates the arguments passed to the create_app function."""
    # check catalog path argument and get name
    if not isinstance(catalog_path, Path) and not isinstance(catalog_path, str):
        raise TypeError(
            f'catalog_path must be a Path or str, not {type(catalog_path)}',
        )
    if isinstance(catalog_path, str):
        catalog_path = Path(catalog_path)

    catalog_name: str = catalog_path.name.replace(catalog_path.suffix, '')

    # check catalog type argument
    if not isinstance(catalog_type, str):
        raise TypeError(
            f'catalog_type must be a str, not {type(catalog_type)}',
        )
    catalog_type = catalog_type.lower()
    catalog_implementations = CatalogImplementationFactory.get_all_implementations()
    if not catalog_type in catalog_implementations.keys():
        raise KeyError(
            f'catalog_type={catalog_type} is not in {catalog_implementations.keys()}.',
        )
    catalog_implementation = catalog_implementations[catalog_type]

    # check app name argument
    if not app_name:
        app_name = 'Catalog_Xpublish_Server'
    elif not isinstance(app_name, str):
        raise TypeError(
            f'app_name must be a str, not {type(app_name)}',
        )

    # check plugins list argument
    if not xpublish_plugins:
        xpublish_plugins = []
    if not isinstance(xpublish_plugins, list):
        raise TypeError(
            f'xpublish_plugins must be a list of xpublish.Plugin objects, not {type(xpublish_plugins)}',
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
    fastapi_kwargs: Optional[dict] = None,
    config_logging_dict: Optional[LoggingConfigDict] = None,
) -> FastAPI:
    """Main function to create the server app.

    Args:
        catalog_path: The path to the catalog file (i.e., yaml or json).
        catalog_type: The type of catalog to parse.
        app_name: The name of the app.
        xpublish_plugins: A list of external xpublish plugin classes to use.
        fastapi_kwargs: A dictionary of kwargs passed into fastapi.FastAPI().
        config_logging_dict: A dictionary of logging configuration parameters.
    Returns:
        A FastAPI app object.
    """
    # config logging
    APILogging.config_logger(
        config_dict=config_logging_dict,
    )

    # 0. validate input arguments
    app_inputs: AppComponents = validate_arguments(
        catalog_path=catalog_path,
        catalog_type=catalog_type,
        app_name=app_name,
        xpublish_plugins=xpublish_plugins,
    )

    # 1. parse catalog using appropriate catalog search method
    logger.info(
        f'Spinning up server from {catalog_type} catalog at {catalog_path}.',
    )
    catalog_searcher = app_inputs.catalog_implementation.catalog_search(
        catalog_path=catalog_path,
    )
    catalog_endpoints: List[CatalogEndpoint] = catalog_searcher.parse_catalog()

    # 2. Start a Xpublish server
    if not isinstance(fastapi_kwargs, dict):
        fastapi_kwargs = {}
    if 'title' in fastapi_kwargs:
        logger.warn(
            f'Overwriting title={fastapi_kwargs["title"]} with title={app_inputs.name}! '
            'Use param:app_name to set the title of the app, not param:faskapi_kwargs.',
        )
        del fastapi_kwargs['title']
    app = FastAPI(title=app_inputs.name, **fastapi_kwargs)

    # 2. Iterate through the endpoints and add them to the server
    for cat_end in catalog_endpoints:
        cat_prefix = cat_end.catalog_path
        if cat_prefix == '/':
            cat_prefix = ''

        # 2.1 if the endpoint has data, mount a Xpublish server
        if cat_end.contains_datasets:
            rest_server = xpublish.Rest()
            xpublish_title_kwarg = {
                'title': app_inputs.catalog_name + cat_prefix,
            }
            app_kws = {
                **xpublish_title_kwarg,
                **fastapi_kwargs,               
            }
            logger.info(
                f'Adding FastAPI kwargs {app_kws}'
            )
            rest_server.init_app_kwargs(
                app_kws=app_kws
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

            # if cat_prefix == '', xpublish changes the name to the name of the plugin
            if (bool(cat_prefix) and cat_prefix not in rest_server.plugins) | (not cat_prefix and provider_plugin.name not in rest_server.plugins):
                logger.warn(
                    f'Could not add dataset provider plugin for {cat_prefix} to the server!',
                )
                continue

            # add all non-dataset provider plugins
            for plugin in app_inputs.xpublish_plugins:
                assert issubclass(plugin, xpublish.Plugin)
                plugin = plugin()
                if plugin.name not in rest_server.plugins:
                    try:
                        rest_server.register_plugin(
                            plugin=plugin,
                        )
                        assert plugin.name in rest_server.plugins
                        logger.info(
                            f'Added Xpublish plugin={plugin.name} to the server.',
                        )
                    except AssertionError:
                        logger.warn(
                            f'Could not add Xpublish plugin={plugin} to the server.',
                        )
                        continue

            # add the base router (for some reason this needs to come after)
            router = app_inputs.catalog_implementation.catalog_router(
                catalog_endpoint_obj=cat_end,
                prefix='',
            )
            rest_server.app.include_router(router=router.router)

            # mount to the main application
            logger.info(
                f'Mounting a Xpublish server @ {cat_prefix} to the main application.',
            )
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
    logger.info(
        f'Returning successfully created server application!',
    )
    return app
