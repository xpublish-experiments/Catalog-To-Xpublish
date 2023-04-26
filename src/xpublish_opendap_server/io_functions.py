"""
Read data from catalogs into xarray datasets.
"""

import intake
import intake_xarray
import xarray as xr
import fsspec
import string
import abc
from pathlib import Path
from typing import (
    Dict,
    Union,
    Any,
)


def fsspec_open_dataset(
    file_system: fsspec.AbstractFileSystem,
    data_path: str,
    engine: str,
) -> fsspec.core.OpenFile:
    # zarr files must be opened as a mapping
    if engine == 'zarr':
        return fsspec.mapping.FSMap(
            data_path,
            file_system,
        )

    # all other files can be opened as a file
    else:
        return file_system.open(data_path)


class CatalogToXarray(abc.ABC):

    @abc.abstractproperty
    def get_engine_dict(self) -> Dict[str, str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_xarray_engine(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_filesystem(self) -> fsspec.AbstractFileSystem:
        raise NotImplementedError

    @abc.abstractmethod
    def write_attributes(
        self,
        ds: xr.Dataset,
    ) -> xr.Dataset:
        raise NotImplementedError

    @abc.abstractmethod
    def get_dataset_from_catalog(
        self,
        catalog_item_name: str,
    ) -> xr.Dataset:
        raise NotImplementedError


class IntakeToXarray(CatalogToXarray):

    def __init__(
        self,
        catalog_yaml_path: Path,
    ) -> None:

        # create an intake catalog object
        if catalog_yaml_path:
            self.catalog: intake.catalog.Catalog = intake.open_catalog(
                catalog_yaml_path,
            )

    @property
    def get_engine_dict(self) -> Dict[str, str]:
        return {
            'netcdf': 'h5netcdf',
            'ndzarr': 'zarr',
            'zarr': 'zarr',
            'numpy': 'scipy',
            'rasterio': 'rasterio',
        }

    def get_xarray_engine(self) -> Union[str, None]:
        """Get the xarray.open_dataset() engine from the catalog object."""

        # verify the necessary driver plugin is installed
        driver: str = self.catalog.describe()['driver'][0]
        if driver not in intake.registry.keys():
            raise ValueError(
                f'{driver} driver not installed. '
                f'Please install the necessary intake plugin!'
            )
        return self.get_engine_dict.get(driver, None)

    def get_filesystem(self) -> fsspec.AbstractFileSystem:
        """Get the file system from the catalog object."""
        # get the endpoint type
        endpoint_key: str = self.catalog.urlpath.split(':')[0]
        if endpoint_key not in ['s3', 'https']:
            if endpoint_key in list(string.ascii_uppercase):
                endpoint_key = 'file'
            else:
                raise ValueError(
                    f'Endpoint type {endpoint_key} not supported. '
                    f'Please use s3, https, or file.'
                )

        # get storage options
        try:
            storage_options: self.catalog.describe()['args']['storage_options']
        except KeyError:
            storage_options = {}

        # start an appropriate filesystem
        return fsspec.filesystem(
            endpoint_key,
            **storage_options,
        )

    def write_attributes(
        self,
        ds: xr.Dataset,
    ) -> xr.Dataset:
        """Write attributes from the catalog object to the dataset."""

        info_dict = self.catalog.describe()
        if 'name' in info_dict.keys():
            ds.name = info_dict['name']
        if 'description' in info_dict.keys():
            ds.attrs['description'] = info_dict['description']
        ds.attrs['url_path'] = self.catalog.urlpath

        return ds

    def get_dataset_from_catalog(
        self,
        catalog_item_name: str,
    ) -> xr.Dataset:

        # find the object in the catalog (sub-catalog)
        try:
            intake_catalog_obj: intake.catalog.Catalog = self.catalog[catalog_item_name]
            info_dict: Dict[str, Any] = intake_catalog_obj.describe()
        except KeyError:
            raise KeyError(f'{catalog_item_name} not found in catalog.')

        # verify the object is readable by xarray
        if info_dict['container'] != 'xarray':
            raise ValueError(
                f'{catalog_item_name} is not readable by xarray. '
                f'Container={info_dict["container"]}'
            )

        # open the file with fsspec
        file_system = self.get_filesystem()
        engine = self.get_xarray_engine()
        open_file = fsspec_open_dataset(
            file_system=file_system,
            file_path=info_dict['args']['urlpath'],
            engine=engine,
        )

        # open as a xarray dataset and add attributes
        ds: xr.Dataset = xr.open_dataset(
            open_file,
            engine=engine,
        )

        ds = self.write_attributes(ds)

        # return the dataset
        return ds
