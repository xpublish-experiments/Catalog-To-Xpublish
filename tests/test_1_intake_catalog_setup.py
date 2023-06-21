"""A pytest module for testing whether Intake catalog setup functions are working properly."""
import intake
import pytest
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


def test_factory() -> None:
    assert isinstance(IntakeCatalogSearch, CatalogSearcherClass)
    assert isinstance(IntakeToXarray, CatalogIOClass)
    assert isinstance(IntakeRouter, CatalogRouterClass)
    assert 'intake' in CatalogImplementationFactory.get_all_implementations().keys()

    obj = CatalogImplementationFactory.get_catalog_implementation('intake')
    assert isinstance(obj, CatalogImplementation)


# @pytest.fixture(scope='session')
def test_catalog_classes(
    catalog_path: Path,
) -> None:
    """Tests parsing of an intake catalog."""

    # get implementation
    obj = CatalogImplementationFactory.get_catalog_implementation('intake')

    # check that we can build a catalog object from .yaml
    seacher = obj.catalog_search(catalog_path=catalog_path)

    assert isinstance(seacher.catalog_object, intake.Catalog)
    assert seacher.suffixes == ['.nc', '.zarr']
    assert seacher.catalog_object.name == 'test_intake_zarr_catalog'
    assert seacher.catalog_object.path == str(catalog_path)

    # check that we can parse the catalog
    catalog_endpoints: List[CatalogEndpoint] = seacher.parse_catalog()

    assert isinstance(catalog_endpoints, list)
    assert len(catalog_endpoints) >= 1
    assert isinstance(catalog_endpoints[0], CatalogEndpoint)

    # check that the parser finds valid datasets
    for cat_end in catalog_endpoints:
        if cat_end.contains_datasets:
            assert len(cat_end.dataset_ids) >= 1

            for i, ds_name in enumerate(cat_end.dataset_ids):
                assert isinstance(ds_name, str)
                assert ds_name in cat_end.dataset_info_dicts.keys()
                if i == 0:
                    # check if we can read a dataset
                    io_class = obj.catalog_to_xarray(
                        catalog_obj=cat_end.catalog_obj,
                    )
                    ds = io_class.get_dataset_from_catalog(dataset_id=ds_name)
                    assert isinstance(ds, xr.Dataset)
                    assert ds_name == ds.attrs['name']
