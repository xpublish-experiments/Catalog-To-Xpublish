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
    return home_dir / 'test_catalogs' / 'sample_stac_catalog' / 'catalog.json'


def test_factory() -> None:
    assert isinstance(STACCatalogSearch, CatalogSearcherClass)
    assert isinstance(STACToXarray, CatalogIOClass)
    assert isinstance(STACRouter, CatalogRouterClass)
    assert 'stac' in CatalogImplementationFactory.get_all_implementations().keys()

    obj = CatalogImplementationFactory.get_catalog_implementation('stac')
    assert isinstance(obj, CatalogImplementation)


def test_catalog_classes(
    catalog_path: str,
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
            assert len(cat_end.dataset_ids) == 0
        else:
            assert len(cat_end.dataset_ids) >= 1

        for ds_name in cat_end.dataset_ids:
            assert isinstance(ds_name, str)
            assert ds_name in cat_end.dataset_info_dicts.keys()
