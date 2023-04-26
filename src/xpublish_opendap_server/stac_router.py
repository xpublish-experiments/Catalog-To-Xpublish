from pystac_client import Client
from fastapi import APIRouter
from typing import (
    Optional,
)


def _add_subcatalog_routes(
    router: APIRouter,
    catalog: Client,
    parent_path: Optional[str] = None,
) -> None:
    """Adds sub-routes for all sub-catalogs to a FastAPI router."""
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
    router = APIRouter()

    client = Client.open(catalog_url)
    _add_subcatalog_routes(client.get_root_catalog())

    return router
