"""A pytest module for testing whether Intake catalog setup functions are working properly."""
import intake
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
    IntakeCatalogSearch,
)
from catalog_to_xpublish.io import (
    IntakeToXarray,
)
from catalog_to_xpublish.routers import (
    IntakeRouter,
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
    return home_dir / 'test_catalogs' / \
        'test_intake_zarr_catalog.yaml'


@pytest.fixture(scope='session')
def catalog_implementation() -> CatalogImplementation:
    obj = CatalogImplementationFactory.get_catalog_implementation('intake')
    assert isinstance(obj, CatalogImplementation)
    return obj


def test_factory() -> None:
    assert isinstance(IntakeCatalogSearch, CatalogSearcherClass)
    assert isinstance(IntakeToXarray, CatalogIOClass)
    assert isinstance(IntakeRouter, CatalogRouterClass)
    assert 'intake' in CatalogImplementationFactory.get_all_implementations().keys()


def test_catalog_classes(
    catalog_path: Path,
    catalog_implementation: CatalogImplementation,
) -> None:
    """Tests parsing of an intake catalog."""

    # shorten name for convenience
    obj = catalog_implementation

    # check that we can build a catalog object from .yaml
    searcher = obj.catalog_search(catalog_path=catalog_path)

    assert isinstance(searcher.catalog_object, intake.Catalog)
    assert searcher.suffixes == ['.nc', '.zarr']
    assert searcher.catalog_object.name == 'test_intake_zarr_catalog'
    assert searcher.catalog_object.path == str(catalog_path)

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
