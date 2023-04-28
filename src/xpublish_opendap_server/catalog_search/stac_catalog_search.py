from pystac_client import Client
from xpublish_opendap_server.catalog_search.base import (
    CatalogSearcher,
    CatalogEndpoint,
)
from typing import (
    List,
    Optional,
)


class STACCatalogSearch(CatalogSearcher):

    def build_catalog_object(
        self,
        catalog_path: str,
    ) -> Client:
        """Builds a catalog object."""
        return Client.open(catalog_path)

    def parse_catalog(
        self,
        catalog: Client,
        parent_path: Optional[str] = None,
        list_of_catalog_endpoints: Optional[List[CatalogEndpoint]] = None,
    ) -> List[CatalogEndpoint]:
        raise NotImplementedError


def _add_subcatalog_routes(
    router: APIRouter,
    catalog: Client,
    parent_path: Optional[str] = None,
) -> None:
    """Adds sub-routes for all sub-catalogs to a FastAPI router."""
    # TODO: come back to this once we have a suitable STAC catalog with storage info
    raise NotImplementedError
    if parent_path is None:
        parent_path = ''

    for child in catalog.get_children():
        path = parent_path + '/' + child.id

        if child.assets:
            dataset_router = dataset_router(child.get_self_href())
            router.include_router(dataset_router, prefix=path)

        else:
            subcatalog = catalog.get_catalog(child.get_self_href())
            subcatalog_router = stac_catalog_router(
                subcatalog.get_self_href(),
            )
            router.include_router(subcatalog_router, prefix=path)

        _add_subcatalog_routes(
            router,
            child,
            parent_path=path,
        )


def stac_catalog_router(catalog_url: str) -> APIRouter:
    """Creates a FastAPI router for a STAC catalog.

    All sub-catalogs are traversed recursively and a router is created for each.

    Arguments:
        catalog_url: URL of the STAC catalog (.json endpoint).

    Returns:
        FastAPI router for the STAC catalog.
    """
    # TODO: come back to this once we have a suitable STAC catalog with storage info
    raise NotImplementedError
    router = APIRouter()

    client = Client.open(catalog_url)
    _add_subcatalog_routes(client.get_root_catalog())

    return router
