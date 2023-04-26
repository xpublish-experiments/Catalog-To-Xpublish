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


class CatalogToXarray(abc.ABC):

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
        catalog_yaml_path: Union[Path, str],
    ) -> None:

        # create an intake catalog object
        if catalog_yaml_path:
            catalog_yaml_path = Path(catalog_yaml_path)
            self.catalog: intake.catalog.Catalog = intake.open_catalog(
                catalog_yaml_path,
            )
        else:
            raise ValueError(
                'Please provide a valid input to create a catalog object! .'
                'I.e., a path to a yaml file or a yaml string.'
            )

    def write_attributes(
        self,
        ds: xr.Dataset,
    ) -> xr.Dataset:
        """Write attributes from the catalog object to the dataset."""

        info_dict = self.catalog.describe()
        if 'name' in info_dict.keys():
            ds['name'] = info_dict['name']
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
            intake_catalog_obj: intake.source.base.DataSource = self.catalog[catalog_item_name]
            info_dict: Dict[str, Any] = intake_catalog_obj.describe()
        except KeyError:
            raise KeyError(f'{catalog_item_name} not found in catalog.')

        # verify the object is readable by xarray
        if info_dict['container'] != 'xarray':
            raise ValueError(
                f'{catalog_item_name} is not readable by xarray. '
                f'Container={info_dict["container"]}'
            )

        # verify the necessary driver plugin is installed
        driver: str = info_dict['driver'][0]
        if driver not in intake.registry.keys():
            raise ValueError(
                f'{driver} driver not installed. '
                f'Please install the necessary intake plugin!'
            )

        # open as a xarray dataset and add attributes
        ds: xr.Dataset = intake_catalog_obj.to_dask()
        ds = self.write_attributes(ds)

        # return the dataset
        return ds


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
        catalog_item_name: str,
    ) -> xr.Dataset:
        raise NotImplementedError
