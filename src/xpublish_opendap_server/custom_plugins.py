import xarray as xr
# NOTE: I had to add a import dask.array line to zarr.py in the xpublish source code.
# a bit wierd... since I can just get dask.array.Array in my terminal

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
from pydantic import (
    Field,
    BaseConfig,
    validator,
)


class DatasetProviderPlugin(Plugin):
    """A dataset router plugin for the xpublish-opendap-server.

    This should be instantiated for each CatalogEndpoint object.
    """
    name = 'catalog-endpoint-provider'
    catalog_endpoint_obj: CatalogEndpoint = Field(
        ..., alias='catalog_endpoint_obj')
    io_class: CatalogToXarray = Field(..., alias='io_class')

    class Config(BaseConfig):
        arbitrary_types_allowed = True

    @validator('catalog_endpoint_obj', pre=True)
    def check_endpoint_class(cls, v) -> CatalogEndpoint:
        if not isinstance(v, CatalogEndpoint):
            raise ValueError(
                'catalog_endpoint_obj must be an instance of CatalogEndpoint',
            )
        return v

    @validator('io_class', pre=True)
    def check_io_class(cls, v) -> CatalogToXarray:
        if not isinstance(v, CatalogToXarray):
            raise ValueError(
                'io_class must be an instance of CatalogToXarray',
            )
        return v

    @classmethod
    def from_endpoint(
        cls,
        catalog_endpoint: CatalogEndpoint,
        io_class: CatalogToXarray,
    ) -> 'DatasetProviderPlugin':
        io_class_instance = io_class(
            catalog_obj=catalog_endpoint.catalog_obj,
        )
        return cls(**
                   {
                       'catalog_endpoint_obj': catalog_endpoint,
                       'io_class': io_class_instance,
                   },
                   )

    @hookimpl
    def get_datasets(self) -> List[str]:
        return self.catalog_endpoint_obj.dataset_ids

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
