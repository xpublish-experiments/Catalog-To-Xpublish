import xarray as xr
from xpublish_opendap_server.catalog_search import (
    CatalogEndpoint,
)
from xpublish_opendap_server.io_classes import (
    CatalogToXarray,
)
from fastapi import (
    APIRouter,
    Depends,
)
from xpublish import (
    Plugin,
    hookimpl,
    Dependencies,
)
from typing import (
    List,
)


class DatasetProviderPlugin(Plugin):
    """A dataset router plugin for the xpublish-opendap-server.

    This should be instantiated for each CatalogEndpoint object.
    """
    name = 'catalog-endpoint-provider'

    def __init__(
        self,
        catalog_endpoint: CatalogEndpoint,
        io_class: CatalogToXarray,
    ) -> None:

        self.catalog_endpoint_obj = catalog_endpoint
        self.io_class = io_class
        self.catalog_to_xarray = self.io_class(
            catalog_obj=self.catalog_endpoint_obj.catalog_obj,
        )

    @hookimpl
    def get_datasets(self) -> List[str]:
        return self.catalog_endpoint.dataset_ids

    @hookimpl
    def get_dataset(
        self,
        dataset_id: str,
    ) -> xr.Dataset | None:
        if dataset_id in self.catalog_endpoint_obj.dataset_ids:
            return self.io_class.get_dataset_from_catalog(dataset_id)
        return None


class DatasetInfoPlugin(Plugin):
    """A dataset router plugin for the xpublish-opendap-server.

    May be a better implementation than the one above.
    The problem is this expects an xarray dataset ready to go.

    NOTE: NOT IMPLEMENTED YET!
    """
    name = 'dataset-info-provider'

    def __init__(
        self,
        catalog_endpoint: CatalogEndpoint,
        io_class: CatalogToXarray,
    ) -> None:

        self.catalog_endpoint_obj = catalog_endpoint
        self.io_class = io_class
        self.catalog_to_xarray = self.io_class(
            catalog_obj=self.catalog_endpoint_obj.catalog_obj,
        )

    @hookimpl
    def dataset_router(
        self,
        deps: Dependencies,
    ) -> APIRouter:
        router = APIRouter(
            prefix=self.catalog_endpoint_obj.catalog_path,
            tags=[self.catalog_endpoint_obj.catalog_path],
        )

        @router.get('/datasets')
        def list_datasets(dataset=Depends(deps.dataset)):
            return dataset.variables

        return router
