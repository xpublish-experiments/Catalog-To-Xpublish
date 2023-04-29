import xarray as xr
from xpublish_opendap_server.io_classes.base import CatalogToXarray
from pathlib import Path
from typing import (
    Union,
)


class STACToXarray(CatalogToXarray):

    def __init__(
        self,
        catalog_json_path: Union[Path, str],
    ) -> None:
        raise NotImplementedError

    def write_attributes(
        self,
        ds: xr.Dataset,
    ) -> xr.Dataset:
        raise NotImplementedError

    def get_dataset_from_catalog(
        self,
        dataset_id: str,
    ) -> xr.Dataset:
        raise NotImplementedError
