import intake
import xarray as xr
from xpublish_opendap_server.io_classes.base import (
    CatalogToXarray,
)
from pathlib import Path
from typing import (
    Any,
    Dict,
    Optional,
    Union,
)


class IntakeToXarray(CatalogToXarray):

    def __init__(
        self,
        catalog_yaml_path: Optional[Union[Path, str]] = None,
        catalog_obj: Optional[intake.catalog.Catalog] = None,
    ) -> None:

        # create an intake catalog object
        if catalog_yaml_path:
            catalog_yaml_path = Path(catalog_yaml_path)
            self.catalog: intake.catalog.Catalog = intake.open_catalog(
                catalog_yaml_path,
            )
        elif catalog_obj:
            self.catalog: intake.catalog.Catalog = catalog_obj
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
        dataset_id: str,
    ) -> xr.Dataset:

        # find the object in the catalog (sub-catalog)
        try:
            intake_catalog_obj: intake.source.base.DataSource = self.catalog[dataset_id]
            info_dict: Dict[str, Any] = intake_catalog_obj.describe()
        except KeyError:
            raise KeyError(f'{dataset_id} not found in catalog.')

        # verify the object is readable by xarray
        if info_dict['container'] != 'xarray':
            raise ValueError(
                f'{dataset_id} is not readable by xarray. '
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
