import intake
import xarray as xr
from fastapi import APIRouter
from xpublish_opendap_server.io_functions import (
    IntakeToXarray,
)
from typing import (
    Optional,
)


def intake_dataset_router(
    catalog: intake.catalog.Catalog,
) -> APIRouter:
    """Creates a FastAPI router for an intake dataset."""
    router = APIRouter()

    @router.get('/{catalog_item_name}')
    def get_dataset(
        catalog_item_name: str,
    ) -> xr.Dataset:
        """Get the dataset."""
        conversion_obj = IntakeToXarray(catalog_obj=catalog)
        ds = conversion_obj.get_dataset_from_catalog(catalog_item_name)
        return ds

    # TODO: FIGURE OUT HOW TO INCORPORATE THIS WITH OPENDAP
    # seems like you would build it here

    return router


def _add_sub_catalog_routes(
    router: APIRouter,
    catalog: intake.catalog.Catalog,
    parent_path: Optional[str] = None,
) -> None:
    """Adds sub-routes for all sub-catalogs to a FastAPI router."""
    if parent_path is None:
        parent_path = ''

    for child_name, child in catalog.items():
        data_source_found = False
        path = parent_path + '/' + child_name

        if isinstance(child, intake.catalog.Catalog):
            subcatalog_router = intake_catalog_router(
                child,
                base_router=router,
            )
            router.include_router(subcatalog_router, prefix=path)

        elif isinstance(child, intake.source.base.DataSource) and not data_source_found:
            # only add this router once per parent path
            data_source_found = True

            # pass the catalog item containing the dataset to a router
            dataset_router = intake_dataset_router(
                catalog,
            )
            router.include_router(dataset_router, prefix=parent_path)

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
