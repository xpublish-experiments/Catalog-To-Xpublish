import xarray as xr
# NOTE: I had to add a import dask.array line to zarr.py in the xpublish source code.
# a bit wierd... since I can just get dask.array.Array in my terminal

from catalog_to_xpublish.base import (
    CatalogEndpoint,
    CatalogToXarray,
)
from xpublish import (
    Plugin,
    hookimpl,
)
from typing import (
    List,
)
from pydantic import (
    BaseConfig,
)


class DatasetProviderPlugin(Plugin):
    """A dataset router plugin for the xpublish-opendap-server.

    This should be instantiated for each CatalogEndpoint object.
    """
    name: str = 'catalog-endpoint-provider'
    catalog_endpoint_obj: CatalogEndpoint = None
    io_class: CatalogToXarray = None

    class Config(BaseConfig):
        arbitrary_types_allowed = True

    def __init__(
        self,
        catalog_endpoint: CatalogEndpoint,
        io_class: CatalogToXarray,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        # check the input types
        if not isinstance(catalog_endpoint, CatalogEndpoint):
            raise ValueError(
                'catalog_endpoint must be an instance of CatalogEndpoint',
            )

        if not issubclass(io_class, CatalogToXarray):
            raise ValueError(
                'io_class must be a subclass of CatalogToXarray',
            )

        # init the class variables
        self.catalog_endpoint_obj = catalog_endpoint
        self.io_class = io_class(
            catalog_obj=self.catalog_endpoint_obj.catalog_obj,
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
