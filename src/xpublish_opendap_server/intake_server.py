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
    rest_server = xpublish.Rest()

    # 2. Instantiate and register a Dataset Provider plugin object for each CatalogEndpoint
    for cat_end in catalog_endpoints:
        provider_plugin = DatasetProviderPlugin.from_endpoint(
            catalog_endpoint=cat_end,
            io_class=IntakeToXarray,
        )
        rest_server.register_plugin(
            plugin=provider_plugin,
            plugin_name=cat_end.catalog_path,
        )

    # add opendap router plugin
    # NOTE: this doesn't work because it expect a dataset as a dependency
    # rest_server.register_plugin(
    #    OpenDapPlugin,
    #    plugin_name='opendap',
    # )

    # assert our plugins are registered
    for cat_end in catalog_endpoints:
        assert cat_end.catalog_path in rest_server.plugins

    # fire up the server!
    rest_server.serve(
        host=LOCAL_HOST,
        port=LOCAL_PORT,
    )


if __name__ == '__main__':
    main()
