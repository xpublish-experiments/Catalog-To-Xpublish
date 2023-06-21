import logging
import pystac
import fsspec
import string
import xarray as xr
from catalog_to_xpublish.base import CatalogToXarray
from pathlib import Path
from typing import (
    Dict,
    Tuple,
    Union,
    Any,
    Optional,
)
from catalog_to_xpublish.factory import (
    CatalogIOClass,
)

logger = logging.getLogger(__name__)


@CatalogIOClass
class STACToXarray(CatalogToXarray):

    catalog_type: str = 'stac'

    def __init__(
        self,
        catalog_json_path: Optional[Union[Path, str]] = None,
        catalog_obj: Optional[pystac.Collection | pystac.Catalog] = None,
    ) -> None:
        """Initialize the STACToXarray class.

        NOTE: The language is confusing here. The catalog_obj is a pystac.Collection,
            not a pystac.Catalog. This is because we need the get_assets() method.
        """
        # create an STAC catalog object
        if catalog_json_path:
            catalog_json_path = Path(catalog_json_path)
            self.catalog: pystac.Collection = pystac.Collection.from_file(
                catalog_json_path,
            )
        elif isinstance(catalog_obj, pystac.Collection):
            self.catalog: pystac.Collection = catalog_obj
        elif isinstance(catalog_obj, pystac.Catalog):
            self.catalog: pystac.Catalog = catalog_obj
        else:
            raise ValueError(
                'Please provide a valid input to create a catalog object! .'
                'I.e., a path/URL to a json file.',
            )

    def write_attributes(
        self,
        ds: xr.Dataset,
    ) -> xr.Dataset:
        info_dict = self.catalog.to_dict()
        if 'id' in info_dict.keys():
            ds.attrs['name'] = info_dict['id']
        if 'description' in info_dict.keys():
            ds.attrs['description'] = info_dict['description']
        ds.attrs['stac_collection'] = self.catalog.self_href

        return ds

    def _get_asset(
        self,
        dataset_id: str,
    ) -> Tuple[pystac.Asset, Dict[str, Any]]:
        """Return an asset and its info dictionary."""

        # set a key error string
        key_error_str: str = (
            f'{dataset_id} not found in collection/catalog. '
            f'Please check the dataset name and try again.',
        )
        # if out data is in a collection, get it my name
        if isinstance(self.catalog, pystac.Collection):
            try:
                stac_asset: pystac.Asset = self.catalog.get_assets()[
                    dataset_id
                ]
            except KeyError:
                logger.error(key_error_str)
                raise KeyError(key_error_str)

        # if the asset level is an item, get the first asset
        elif isinstance(self.catalog, pystac.Catalog):
            asset_level: pystac.Item = self.catalog.get_item(dataset_id)

            # raise error is empty return
            if not asset_level:
                logger.error(key_error_str)
                raise KeyError(key_error_str)

            # get the first asset
            assets = asset_level.assets.items()
            if len(assets) > 1:
                logger.warning(
                    f'More than one asset found in {dataset_id}. '
                    f'Using the first asset named {list(assets)[0][0]}.',
                )
            elif len(assets) == 0:
                raise ValueError(
                    f'No assets found in {dataset_id}.',
                )
            stac_asset: pystac.Asset = list(assets)[0][1]
        else:
            raise TypeError(
                'The catalog must be a pystac.Collection or pystac.Catalog.',
            )

        # get the info dictionary and return
        info_dict: Dict[str, Any] = stac_asset.to_dict()
        return stac_asset, info_dict

    @staticmethod
    def _read_zarr(
        asset: pystac.Asset,
    ) -> xr.Dataset:
        # get the endpoint type
        endpoint_key: str = asset.href.split(':')[0]
        if endpoint_key not in ['s3', 'https']:
            if endpoint_key in list(string.ascii_uppercase):
                endpoint_key = 'file'
            else:
                raise ValueError(
                    f'Endpoint type {endpoint_key} not supported. '
                    f'Please use s3, https, or file.',
                )

        # get storage options
        try:
            storage_options: dict = asset.extra_fields['xarray:storage_options']
        except KeyError:
            storage_options = {}

        # start an appropriate filesystem
        fs = fsspec.filesystem(
            endpoint_key,
            **storage_options,
        )

        engine: str = asset.extra_fields['xarray:open_kwargs']['engine']
        if engine == 'zarr':
            open_file = fsspec.mapping.FSMap(
                asset.href,
                fs,
            )

        # all other files can be opened as a file
        else:
            open_file = fs.open(asset.href)

        return xr.open_dataset(
            open_file,
            **asset.extra_fields['xarray:open_kwargs'],
        )

    def get_dataset_from_catalog(
        self,
        dataset_id: str,
    ) -> xr.Dataset:
        # find the object in the catalog/collection (sub-catalog)
        logger.info(
            f'Getting dataset {dataset_id} from STAC {self.catalog.STAC_OBJECT_TYPE}.',
        )
        stac_asset, info_dict = self._get_asset(dataset_id)

        # verify the object is readable by xarray
        for key in [
            'xarray:open_kwargs',
            'xarray:storage_options',
        ]:
            if not key in info_dict.keys():
                raise ValueError(
                    f'{dataset_id} is missing the {key} info. ',
                )

        # open as a xarray dataset and add attributes
        ds: xr.Dataset = self._read_zarr(stac_asset)
        ds = self.write_attributes(ds)
        ds.attrs['url_path'] = stac_asset.href

        # return the dataset
        return ds
