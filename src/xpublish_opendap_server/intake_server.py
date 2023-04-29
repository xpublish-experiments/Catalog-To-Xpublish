"""Main server file"""
import xpublish
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
        provider_plugin = DatasetProviderPlugin(
            catalog_endpoint=cat_end,
            io_class=IntakeToXarray,
        )
        rest_server.register_plugin(
            plugin=provider_plugin,
            plugin_name=cat_end.catalog_path,
        )

    rest_server.start_server(
        host=LOCAL_HOST,
        port=LOCAL_PORT,
    )


if __name__ == '__main__':
    main()
