"""Main server file"""
# NOTE: we are using a local version of xpublish (release is missing features we need)
import xpublish
from xpublish_opendap import OpenDapPlugin
from xpublish_opendap_server.catalog_search import (
    CatalogEndpoint,
    IntakeCatalogSearch,
)
from xpublish_opendap_server.io_classes import (
    IntakeToXarray,
)
from xpublish_opendap_server.custom_plugins import (
    DatasetProviderPlugin,
)
from pathlib import Path
from typing import (
    List,
)

LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8000


def main():
    # 1. parse catalog using appropriate catalog search method
    catalog_obj = IntakeCatalogSearch().build_catalog_object(
        catalog_path=Path.cwd() / 'test_catalogs' / 'nested_full_intake_zarr_catalog.yaml'
    )
    catalog_endpoints: List[CatalogEndpoint] = IntakeCatalogSearch().parse_catalog(
        catalog=catalog_obj,
    )

    # 2. Start a Xpublish server
    from fastapi import FastAPI
    app = FastAPI(
        title='Intake Catalog Xpublish Server',
    )
    # rest_server = xpublish.Rest()
    # rest_server.init_app_kwargs(
    #    app_kws={
    #        'title': 'Intake Catalog Xpublish Server',
    #    }
    # )

    # 2. Instantiate and register a Dataset Provider plugin object for each CatalogEndpoint
    for cat_end in catalog_endpoints:
        rest_server = xpublish.Rest()
        provider_plugin = DatasetProviderPlugin.from_endpoint(
            catalog_endpoint=cat_end,
            io_class=IntakeToXarray,
        )
        rest_server.register_plugin(
            plugin=provider_plugin,
            plugin_name=cat_end.catalog_path,
        )

        # add opendap router plugin
        rest_server.register_plugin(
            OpenDapPlugin(),
            plugin_name='opendap',
        )

        # mount to the main application
        app.mount(
            path=cat_end.catalog_path,
            app=rest_server.app,
        )
    app.openapi()
    return app


if __name__ == '__main__':
    app = main()
    import uvicorn
    uvicorn.run(
        app,
        host=LOCAL_HOST,
        port=LOCAL_PORT,
        # reload=True,
    )
