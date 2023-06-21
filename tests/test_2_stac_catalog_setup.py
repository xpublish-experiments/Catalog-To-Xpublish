"""A pytest module for testing whether STAC catalog setup functions are working properly."""
import pystac
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
    STACCatalogSearch,
)
from catalog_to_xpublish.io import (
    STACToXarray,
)
from catalog_to_xpublish.routers import (
    STACRouter,
)


@pytest.fixture(scope='session')
def catalog_path() -> str:
    return r'https://code.usgs.gov/wma/nhgf/stac/-/raw/main/xpublish_sample_stac/catalog/catalog.json'


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
                    assert f'{cat_end.catalog_obj.id}: {ds_name}' == ds.attrs['name']
