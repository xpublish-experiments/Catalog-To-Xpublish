"""
Read data from catalogs into xarray datasets.
"""

import intake
import intake_xarray
import xarray as xr
import fsspec
import string
from pathlib import Path
from typing import (
    Dict,
    Any,
    Callable,
)

DRIVER_TO_ENGINE = {
    'netcdf': 'h5netcdf',
    'ndzarr': 'zarr',
    'zarr': 'zarr',
    'numpy': 'scipy',
    'rasterio': 'rasterio',
}


def intake_to_xarray(
    intake_catalog: intake.catalog.Catalog,
    catalog_object: str,
) -> xr.Dataset:
    """Read a catalog object into a xarray dataset.

    Arguments:
        intake_catalog: An opened intake catalog.
        catalog_object: The name of catalog object.

    Returns:
        An xarray dataset.
    """
    # find the object in the catalog
    try:
        intake_catalog_obj = intake_catalog[catalog_object]
        info_dict: Dict[str, Any] = intake_catalog_obj.describe()
    except KeyError:
        raise KeyError(f'{catalog_object} not found in catalog.')

    # verify the object is readable by xarray
    if info_dict['container'] != 'xarray':
        raise ValueError(
            f'{catalog_object} is not readable by xarray. '
            f'Container={info_dict["container"]}'
        )

    # verify the necessary driver plugin is installed
    driver: str = info_dict['driver'][0]
    if driver not in intake.registry.keys():
        raise ValueError(
            f'{driver} driver not installed. '
            f'Please install the necessary intake plugin!'
        )

    # convert driver to xarray engine format
    engine: str = DRIVER_TO_ENGINE.get(driver, None)

    # get the endpoint type
    endpoint_key: str = intake_catalog_obj.urlpath.split(':')[0]
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
        storage_options: Dict[str, Any] = info_dict['args']['storage_options']
    except KeyError:
        storage_options = {}

    # start an appropriate filesystem
    fs = fsspec.filesystem(
        endpoint_key,
        **storage_options,
    )

    # zarr files must be opened as a mapping
    if engine is 'zarr':
        open_file = fsspec.mapping.FSMap(
            intake_catalog_obj.urlpath,
            fs,
        )

    # all other files can be opened as a file
    else:
        open_file = fs.open(intake_catalog_obj.urlpath)

    # return as a xarray dataset
    return xr.open_dataset(
        open_file,
        engine=engine,
    )
