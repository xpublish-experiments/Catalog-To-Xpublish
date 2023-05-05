"""Main server file"""
# NOTE: we are using a local version of xpublish (release is missing features we need)
import warnings
import xpublish
from fastapi import FastAPI
import uvicorn
from xpublish_opendap import OpenDapPlugin
from xpublish_opendap_server.catalog_search import (
    CatalogEndpoint,
    IntakeCatalogSearch,
    DatasetProviderPlugin,
)
from xpublish_opendap_server.io_classes import (
    IntakeToXarray,
)
from xpublish_opendap_server.routers import (
    IntakeRouter,
)

from pathlib import Path
from typing import (
    Tuple,
    List,
    Optional,
)

CATALOG_PATH = Path.cwd() / 'test_catalogs' / \
    'nested_full_intake_zarr_catalog.yaml'
APP_NAME = 'Intake_Catalog_Xpublish_Server'
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8000


def validate_arguments(
    catalog_path: Path,
    app_name: Optional[str] = None,
    xpublish_plugins: Optional[List[xpublish.Plugin]] = None,
) -> Tuple[Path, str, list]:
    """Validates the arguments passed to the create_app function."""
    # check catalog path argument
    if not isinstance(catalog_path, Path):
        raise TypeError(
            f'catalog_path must be a Path object, not {type(catalog_path)}'
        )
    if not catalog_path.exists():
        raise FileNotFoundError(
            f'catalog_path={catalog_path} does not exist.'
        )

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

    return catalog_path, app_name, xpublish_plugins


def create_app(
    catalog_path: Path,
    app_name: Optional[str] = None,
    xpublish_plugins: Optional[List[xpublish.Plugin]] = None,
) -> FastAPI:
    """Creates a FastAPI application from an Intake .yaml file."""
    # 0. validate arguments
    catalog_path, app_name, xpublish_plugins = validate_arguments(
        catalog_path=catalog_path,
        app_name=app_name,
        xpublish_plugins=xpublish_plugins,
    )

    # 1. parse catalog using appropriate catalog search method
    intake_searcher = IntakeCatalogSearch(
        catalog_path=catalog_path,
    )
    catalog_name: str = catalog_path.name.replace('.yaml', '')
    catalog_endpoints: List[CatalogEndpoint] = intake_searcher.parse_catalog()

    # 2. Start a Xpublish server
    app = FastAPI(
        title=app_name
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
                    'title': catalog_name + cat_prefix,
                },
            )

            # add dataset provider plugin
            provider_plugin = DatasetProviderPlugin.from_endpoint(
                catalog_endpoint=cat_end,
                io_class=IntakeToXarray,
            )
            rest_server.register_plugin(
                plugin=provider_plugin,
                plugin_name=cat_prefix,
            )

            # add all non-dataset provider plugins
            try:
                for plugin in xpublish_plugins:
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
            router = IntakeRouter(
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
            router = IntakeRouter(
                catalog_endpoint_obj=cat_end,
            )
            app.include_router(router=router.router)
    return app


app = create_app(
    catalog_path=CATALOG_PATH,
    app_name=APP_NAME,
    xpublish_plugins=[OpenDapPlugin],
)


def main() -> None:
    """Main function to run the server."""
    uvicorn.run(
        'intake_server:app',
        host=LOCAL_HOST,
        port=LOCAL_PORT,
        reload=True,
    )


if __name__ == '__main__':
    main()
