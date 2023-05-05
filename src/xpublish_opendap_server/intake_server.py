"""Main server file"""
# NOTE: we are using a local version of xpublish (release is missing features we need)
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
    List,
)

CATALOG_PATH = Path.cwd() / 'test_catalogs' / \
    'nested_full_intake_zarr_catalog.yaml'
APP_NAME = 'Intake_Catalog_Xpublish_Server'
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8000


def create_app(
    catalog_path: Path,
    app_name: str,
) -> FastAPI:
    """Creates a FastAPI application."""
    # 1. parse catalog using appropriate catalog search method
    catalog_obj = IntakeCatalogSearch().build_catalog_object(
        catalog_path=catalog_path,
    )
    catalog_name: str = catalog_path.name.replace('.yaml', '')
    catalog_endpoints: List[CatalogEndpoint] = IntakeCatalogSearch().parse_catalog(
        catalog=catalog_obj,
    )

    # 2. Start a Xpublish server
    app = FastAPI(
        title=app_name
    )

    # 2. Instantiate and register a Dataset Provider plugin object for each CatalogEndpoint
    for cat_end in catalog_endpoints:
        cat_prefix = cat_end.catalog_path
        if cat_prefix == '/':
            cat_prefix = ''

        # if the endpoint has data, mount a Xpublish server
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

            # add opendap router plugin
            rest_server.register_plugin(
                OpenDapPlugin(),
            )
            assert 'opendap' in rest_server.plugins

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
