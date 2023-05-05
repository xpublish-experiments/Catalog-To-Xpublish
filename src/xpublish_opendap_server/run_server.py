"""Main server file"""
import warnings
import xpublish
# NOTE: we are using a local version of xpublish (release is missing features we need)
from fastapi import FastAPI
import uvicorn
from xpublish_opendap import OpenDapPlugin
from xpublish_opendap_server.catalog_search import (
    CatalogEndpoint,
    DatasetProviderPlugin,
)
from xpublish_opendap_server.shared import (
    validate_arguments,
    AppComponents,
)
from pathlib import Path
from typing import (
    List,
    Optional,
)

CATALOG_TYPE: str = 'intake'  # or 'stac'
CATALOG_PATH = Path.cwd() / 'test_catalogs' / \
    'nested_full_intake_zarr_catalog.yaml'
APP_NAME = 'Xpublish Server'
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8000


def create_app(
    catalog_path: Path,
    catalog_type: str = CATALOG_TYPE,
    app_name: Optional[str] = None,
    xpublish_plugins: Optional[List[xpublish.Plugin]] = None,
) -> FastAPI:
    """Creates a FastAPI application from an Intake .yaml file."""
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


app = create_app(
    catalog_path=CATALOG_PATH,
    app_name=APP_NAME,
    xpublish_plugins=[OpenDapPlugin],
)


def main() -> None:
    """Main function to run the server."""
    uvicorn.run(
        'run_server:app',
        host=LOCAL_HOST,
        port=LOCAL_PORT,
        reload=True,
    )


if __name__ == '__main__':
    main()
