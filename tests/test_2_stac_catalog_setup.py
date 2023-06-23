"""A pytest module for testing whether STAC catalog setup functions are working properly."""
import pystac
import pytest
import boto3
import warnings
import xarray as xr
from pathlib import Path
from typing import (
    List,
)
from catalog_to_xpublish.factory import (
    CatalogSearcherClass,
    CatalogIOClass,
    CatalogRouterClass,
    CatalogImplementation,
    CatalogImplementationFactory,
)
from catalog_to_xpublish.base import (
    CatalogEndpoint,
)
from catalog_to_xpublish.searchers import (
    STACCatalogSearch,
)
from catalog_to_xpublish.io import (
    STACToXarray,
)
from catalog_to_xpublish.routers import (
    STACRouter,
)


@pytest.fixture(scope='session')
def aws_credentials() -> bool:
    """Whether we have active AWS credentials or not.

    If we do, return True. If not, return False.
    If False, tests will only be ran on OSN data.
    """
    try:
        boto3.client('s3')
        return True
    except Exception:
        return False


@pytest.fixture(scope='session')
def catalog_path() -> str:
    return r'https://code.usgs.gov/wma/nhgf/stac/-/raw/main/xpublish_sample_stac/catalog/catalog.json'


def does_requester_pay(
    io_class: STACToXarray,
    ds_name: str,
) -> bool:
    """Returns whether a dataset is in a requester pays bucket."""
    stac_asset = io_class._get_asset(ds_name)[0]

    extra_fields: dict = getattr(
        stac_asset,
        'extra_fields',
        {},
    )

    storage_options: dict = extra_fields.get(
        'xarray:storage_options',
        {},
    )

    return storage_options.get('requester_pays', False)


def test_factory() -> None:
    assert isinstance(STACCatalogSearch, CatalogSearcherClass)
    assert isinstance(STACToXarray, CatalogIOClass)
    assert isinstance(STACRouter, CatalogRouterClass)
    assert 'stac' in CatalogImplementationFactory.get_all_implementations().keys()

    obj = CatalogImplementationFactory.get_catalog_implementation('stac')
    assert isinstance(obj, CatalogImplementation)


def test_catalog_classes(
    catalog_path: str,
    aws_credentials: bool,
) -> None:
    """Tests parsing of an STAC catalog."""

    # get implementation
    obj = CatalogImplementationFactory.get_catalog_implementation('stac')

    # check that we can build a catalog object from .yaml
    searcher = obj.catalog_search(catalog_path=catalog_path)

    assert type(searcher.catalog_object) in [pystac.Collection, pystac.Catalog]
    assert searcher.suffixes == ['.nc', '.zarr']
    assert searcher.catalog_object.id == 'nhgf-stac-catalog'
    assert searcher.catalog_object.self_href == str(catalog_path)

    # check that we can parse the catalog
    catalog_endpoints: List[CatalogEndpoint] = searcher.parse_catalog()

    assert isinstance(catalog_endpoints, list)
    assert len(catalog_endpoints) >= 1
    assert isinstance(catalog_endpoints[0], CatalogEndpoint)

    # check that the parser finds valid datasets
    for cat_end in catalog_endpoints:
        if not cat_end.contains_datasets:
            continue

        assert len(cat_end.dataset_ids) >= 1

        for ds_name in cat_end.dataset_ids:
            assert isinstance(ds_name, str)
            assert ds_name in cat_end.dataset_info_dicts.keys()

            # check if we can read a dataset
            tested_ds = False
            i = 0
            while not tested_ds:
                if i == len(cat_end.dataset_ids):
                    warnings.warn(
                        f'Could not find a dataset that can be read for catalog '
                        f'{cat_end.catalog_obj.name}. Test coverage is not complete.'
                    )
                    break
                ds_name = cat_end.dataset_ids[i]
                io_class = obj.catalog_to_xarray(
                    catalog_obj=cat_end.catalog_obj,
                )

                # skip if we have a requester pays bucket and no credentials
                requester_pays: bool = does_requester_pay(
                    io_class=io_class,
                    ds_name=ds_name,
                )
                if requester_pays and not aws_credentials:
                    warnings.warn(
                        'Skipping dataset because it is in a requester pays bucket '
                        'and we do not have AWS credentials.',
                    )
                    i += 1
                    continue

                tested_ds = True
                ds = io_class.get_dataset_from_catalog(dataset_id=ds_name)
                assert isinstance(ds, xr.Dataset)
                assert f'{cat_end.catalog_obj.id}: {ds_name}' == ds.attrs['name']
