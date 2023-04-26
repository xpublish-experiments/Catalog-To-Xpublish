import intake
from fastapi import APIRouter
from typing import (
    Optional,
)


def _add_sub_catalog_routes(
    router: APIRouter,
    catalog: intake.catalog.Catalog,
    parent_path: Optional[str] = None,
) -> None:
    """Adds sub-routes for all sub-catalogs to a FastAPI router."""
    if parent_path is None:
        parent_path = ''

    for child_name, child in catalog.items():
        path = parent_path + '/' + child_name

        if isinstance(child, intake.catalog.Catalog):
            subcatalog_router = intake_catalog_router(
                child,
                base_router=router,
            )
            router.include_router(subcatalog_router, prefix=path)

        elif isinstance(child, intake.source.base.DataSource):
            dataset_router = dataset_router(child)
            router.include_router(dataset_router, prefix=path)

        _add_sub_catalog_routes(
            router,
            child,
            parent_path=path,
        )


def intake_catalog_router(
    catalog_url: str,
    base_router: Optional[APIRouter] = None,
) -> APIRouter:
    """Creates a FastAPI router for an intake catalog."""
    router = APIRouter()

    if base_router:
        router.include_router(base_router)

    catalog = intake.open_catalog(catalog_url)
    _add_sub_catalog_routes(
        router,
        catalog,
    )

    return router
