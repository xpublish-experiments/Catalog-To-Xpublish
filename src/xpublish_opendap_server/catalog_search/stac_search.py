from pystac_client import Client
from xpublish_opendap_server.catalog_search.base import (
    CatalogSearcher,
    CatalogEndpoint,
)
from xpublish_opendap_server.factory import (
    CatalogSearcherClass,
)
from pathlib import Path
from typing import (
    List,
    Dict,
    Optional,
    Any,
)

# TODO: Make a test STAC catalog and get this to work


@CatalogSearcherClass
class STACCatalogSearch(CatalogSearcher):
    """STAC Catalog searcher."""
    catalog_type: str = 'stac'

    def __init__(
        self,
        catalog_path: Optional[Path | str] = None,
    ) -> None:
        """Initializes the catalog searcher."""
        self.__catalog_path = catalog_path
        self.__suffixes = None
        self.__catalog_obj = None

    @property
    def catalog_path(self) -> Path:
        if isinstance(self.__catalog_path, str):
            self.__catalog_path = Path(self.__catalog_path)
        if not isinstance(self.__catalog_path, Path):
            raise TypeError(
                f'Please provide a valid intake catalog .json file path or URL! '
                f'Expected a str or Path, got {type(self.__catalog_path)}'
            )
        if not self.__catalog_path.exists():
            raise FileNotFoundError(
                f'Please provide a valid intake catalog .json file path or URL! '
                f'Could not find {self.__catalog_path}'
            )
        if self.__catalog_path.suffix != '.json':
            raise ValueError(
                f'Please provide a valid intake catalog .json file path or URL! '
                f'File suffix must be .json, not {self.__catalog_path.suffix}'
            )
        return self.__catalog_path

    @property
    def suffixes(self) -> List[str]:
        if self.__suffixes is None:
            self.__suffixes = [
                '.nc',
                '.zarr',
            ]
        return self.__suffixes

    @property
    def catalog_object(self) -> object:
        raise NotImplementedError

    def parse_catalog(
        self,
        catalog: Optional[object] = None,
        parent_path: Optional[str] = None,
        list_of_catalog_endpoints: Optional[List[CatalogEndpoint]] = None,
    ) -> List[CatalogEndpoint]:
        """Recursively searches a catalog for a search term."""
        raise NotImplementedError

# for child in catalog.get_children():
#    path = parent_path + '/' + child.id
#
#    if child.assets:
#        dataset_router = dataset_router(child.get_self_href())
#        router.include_router(dataset_router, prefix=path)
#
#    else:
#        subcatalog = catalog.get_catalog(child.get_self_href())
#        subcatalog_router = stac_catalog_router(
#            subcatalog.get_self_href(),


if __name__ == '__main__':
    catalog_obj = STACCatalogSearch().build_catalog_object(
        catalog_path=Path.cwd() / 'test_catalogs' / 'nested_full_intake_zarr_catalog.yaml'
    )
    list_of_cats = STACCatalogSearch().parse_catalog(
        catalog=catalog_obj,
    )
    print(list_of_cats)
