"""A pytest module for testing intake catalog to xarray dataset conversion."""
import intake
import pytest
from pathlib import Path
from typing import (
    List,
)
from catalog_to_xpublish.catalog_search import (
    CatalogEndpoint,
    IntakeCatalogSearch,
    CatalogSearcher,

)

if Path.cwd().name == 'Xpublish-OPeNDAP-Server':
    home_dir = Path.cwd()
elif Path.cwd().name == 'testing':
    home_dir = Path.cwd().parent
else:
    raise FileNotFoundError(
        'Please run this test from the root directory of the repository.',
    )
CATALOG_PATH = home_dir / 'test_catalogs' / \
    'test_intake_zarr_catalog.yaml'


def test_catalog_search_obj() -> None:
    """Tests that all methods we expect are in our IntakeCatalogSearch object."""
    assert IntakeCatalogSearch.__name__ == 'IntakeCatalogSearch'
    assert IntakeCatalogSearch.suffixes == ['.nc', '.zarr']
    # assert isinstance(IntakeCatalogSearch, CatalogSearcher)
    for func in CatalogSearcher.__abstractmethods__:
        assert hasattr(IntakeCatalogSearch, func)


@pytest.fixture(scope='session')
def test_catalog_parsing(
    catalog_path: Path = CATALOG_PATH,
) -> None:
    """Tests parsing of an intake catalog."""
    # check that we can build a catalog object from .yaml
    catalog_obj_1: intake.Catalog = IntakeCatalogSearch().build_catalog_object(
        catalog_path=catalog_path,
    )
    assert isinstance(catalog_obj_1, intake.Catalog)
    assert catalog_obj_1.name == 'nested_full_intake_zarr_catalog'
    assert catalog_obj_1.path == str(catalog_path)

    # check that we can parse the catalog
    catalog_endpoints: List[CatalogEndpoint] = IntakeCatalogSearch().parse_catalog(
        catalog=catalog_obj_1,
    )
    assert isinstance(catalog_endpoints, list)
    assert len(catalog_endpoints) >= 1
    assert isinstance(catalog_endpoints[0], CatalogEndpoint)

    # 2. Instantiate and register a Dataset Provider plugin object for each CatalogEndpoint
    for cat_end in catalog_endpoints:
        if cat_end.contains_datasets:
            assert len(cat_end.dataset_ids) >= 1

            for ds_name in cat_end.dataset_ids:
                assert isinstance(ds_name, str)
                assert ds_name in cat_end.dataset_info_dicts.keys()


if __name__ == '__main__':
    test_catalog_search_obj()
    test_catalog_parsing()
