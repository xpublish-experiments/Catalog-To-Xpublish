import pytest
import boto3
import xarray as xr
import warnings
from catalog_to_xpublish.factory import (
    CatalogImplementationFactory,
)
from catalog_to_xpublish.io import (
    STACToXarray,
)
from catalog_to_xpublish.base import (
    CatalogEndpoint,
)
from typing import (
    List,
)


@pytest.fixture(scope='session')
def catalog_path() -> str:
    return r'https://code.usgs.gov/wma/nhgf/stac/-/raw/main/xpublish_sample_stac/catalog/catalog.json'


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


def test_read_from_stac(
    catalog_path: str,
    aws_credentials: bool,
) -> None:
    """Tests parsing of an STAC catalog."""

    # check for AWS credentials
    if not aws_credentials:
        raise ValueError(
            'No AWS credentials found! This test cannot be ran.',
        )

    # get implementation
    obj = CatalogImplementationFactory.get_catalog_implementation('stac')

    # check that we can build a catalog object from .yaml
    searcher = obj.catalog_search(catalog_path=catalog_path)

    # check that we can parse the catalog
    catalog_endpoints: List[CatalogEndpoint] = searcher.parse_catalog()

    # check that the parser finds valid datasets
    for cat_end in catalog_endpoints:
        if not cat_end.contains_datasets:
            continue

        # check if we can read a dataset
        tested_ds = False
        i = 0

        while not tested_ds:
            if i == len(cat_end.dataset_ids):
                warnings.warn(
                    f'Could not find a non-requester pays dataset that can be '
                    f'read for catalog {cat_end.catalog_obj.name}. '
                    f'Test coverage is not complete.',
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
            if requester_pays:
                i += 1
                continue

            # check that the dataset is read ok
            tested_ds = True
            ds = io_class.get_dataset_from_catalog(dataset_id=ds_name)
            assert isinstance(ds, xr.Dataset)
            assert ds_name == ds.attrs['name']
