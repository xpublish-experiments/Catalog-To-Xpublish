"""Tests if we can access OSN data w/o AWS credentials."""
import catalog_to_xpublish
from catalog_to_xpublish.factory import (
    CatalogImplementation,
    CatalogImplementationFactory,
)
from pathlib import Path
import pytest


@pytest.fixture(scope='session')
def catalog_path() -> Path:
    """Returns the path to the test catalog."""
    if Path.cwd().name == 'Catalog-To-Xpublish':
        home_dir = Path.cwd()
    elif Path.cwd().name == 'tests':
        home_dir = Path.cwd().parent
    else:
        raise FileNotFoundError(
            f'Please run this test from the root directory of the repository.',
            f'CWD={Path.cwd()}',
        )
    return home_dir / 'test_catalogs' / 'intake_zarr_catalog_osn.yaml'


@pytest.fixture(scope='session')
def catalog_implementation() -> CatalogImplementation:
    obj = CatalogImplementationFactory.get_catalog_implementation('intake')
    assert isinstance(obj, CatalogImplementation)
    return obj


def test_osn_access(catalog_path) -> None:
    ds_name = 'conus404-hourly-osn'
    obj = CatalogImplementationFactory.get_catalog_implementation('intake')
    searcher = obj.catalog_search(catalog_path=catalog_path)
    catalog_endpoints = searcher.parse_catalog()
    io_class = obj.catalog_to_xarray(
        catalog_obj=catalog_endpoints[0].catalog_obj,
    )
    ds = io_class.get_dataset_from_catalog(ds_name)
