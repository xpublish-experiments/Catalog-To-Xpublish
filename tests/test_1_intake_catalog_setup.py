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


def does_requester_pay(
    io_class: IntakeToXarray,
    ds_name: str,
) -> bool:
    """Check whether an intake dataset is in a requester pays bucket."""
    storage_options: dict = getattr(
        io_class.catalog[ds_name],
        'storage_options',
        {},
    )
    return storage_options.get(
        'requester_pays',
        False,
    )


def test_factory() -> None:
    assert isinstance(IntakeCatalogSearch, CatalogSearcherClass)
    assert isinstance(IntakeToXarray, CatalogIOClass)
    assert isinstance(IntakeRouter, CatalogRouterClass)
    assert 'intake' in CatalogImplementationFactory.get_all_implementations().keys()

    obj = CatalogImplementationFactory.get_catalog_implementation('intake')
    assert isinstance(obj, CatalogImplementation)


def test_catalog_classes(
    catalog_path: Path,
    aws_credentials: bool,
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
                    f'No AWS credentials found (or could not configure). '
                    f'Tests will only be ran on OSN data!',
                )
                i += 1
                continue

            # check that the dataset is read ok
            tested_ds = True
            ds = io_class.get_dataset_from_catalog(dataset_id=ds_name)
            assert isinstance(ds, xr.Dataset)
            assert ds_name == ds.attrs['name']
