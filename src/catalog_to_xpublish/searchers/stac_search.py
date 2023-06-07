import logging
import pystac
from catalog_to_xpublish.base import (
    CatalogSearcher,
    CatalogEndpoint,
)
from catalog_to_xpublish.factory import (
    CatalogSearcherClass,
)
from pathlib import Path
from typing import (
    List,
    Dict,
    Iterator,
    Optional,
    Any,
)

logger = logging.getLogger(__name__)


class IteratorHandler:
    """Used to log errors when iterating over a catalog.

    This allows catalog typos to be skipped.
    """

    def __init__(self, original_iterator: Iterator[Any]):
        self.original_iterator = original_iterator

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                value = next(self.original_iterator)
                return value
            except Exception as e:
                if isinstance(e, StopIteration):
                    raise StopIteration
                else:
                    logger.warning(
                        f'Error while iterating over catalog. Skipping item. '
                        f'Original error: {logging.exception(e)}',
                    )


@CatalogSearcherClass
class STACCatalogSearch(CatalogSearcher):
    """STAC Catalog searcher."""
    catalog_type: str = 'stac'

    def __init__(
        self,
        catalog_path: Optional[Path | str] = None,
    ) -> None:
        """Initializes the catalog searcher."""
        self.__catalog_path: Path | str = catalog_path
        self.__suffixes = None
        self.__catalog_obj = None

    @property
    def catalog_path(self) -> str:
        if isinstance(self.__catalog_path, Path):
            if not self.__catalog_path.exists():
                raise FileNotFoundError(
                    f'Please provide a valid intake catalog .json file path or URL! '
                    f'Could not find {self.__catalog_path}',
                )
            self.__catalog_path = str(self.__catalog_path)

        if not isinstance(self.__catalog_path, str):
            raise TypeError(
                f'Please provide a valid intake catalog .json file path or URL! '
                f'Expected a str or Path, got {type(self.__catalog_path)}',
            )

        if Path(self.__catalog_path).suffix != '.json':
            raise ValueError(
                f'Please provide a valid intake catalog .json file path or URL! '
                f'File suffix must be .json, not {Path(self.__catalog_path).suffix}',
            )
        return str(self.__catalog_path)

    @property
    def suffixes(self) -> List[str]:
        if self.__suffixes is None:
            self.__suffixes = [
                '.nc',
                '.zarr',
            ]
        return self.__suffixes

    @property
    def catalog_object(self) -> pystac.Catalog:
        if self.__catalog_obj is None:
            self.__catalog_obj = pystac.Catalog.from_file(
                str(self.catalog_path),
            )
        return self.__catalog_obj

    def _parse_assets(
        self,
        pystac_obj: pystac.Collection | pystac.Item,
        dataset_ids: List[str],
        dataset_info_dicts: Dict[str, Dict[str, Any]],
    ) -> None:
        """Adds all assets to the list + dict of datasets."""
        for child_name, child in pystac_obj.get_assets().items():
            # make sure the item type is supported
            url_path = child.get_absolute_href()
            if url_path.endswith('/'):
                url_path = url_path[:-1]
            if not any([url_path.endswith(suffix) for suffix in self.suffixes]):
                continue

            # if supported, add it to the list
            if isinstance(pystac_obj, pystac.Item):
                child_name = pystac_obj.id
            dataset_ids.append(child_name)
            dataset_info_dicts[child_name] = child.to_dict()

    def parse_catalog(
        self,
        catalog: Optional[object] = None,
        parent_path: Optional[str] = None,
        list_of_catalog_endpoints: Optional[List[CatalogEndpoint]] = None,
    ) -> List[CatalogEndpoint]:
        """Recursively searches a catalog for a search term."""
        # start things off with the full catalog
        if catalog is None:
            catalog = self.catalog_object
        if parent_path is None:
            parent_path = ''

        if list_of_catalog_endpoints is None:
            list_of_catalog_endpoints = []

        # init some vars to store endpoint data
        dataset_ids: List[str] = []
        dataset_info_dicts: Dict[str, Dict[str, Any]] = {}
        sub_catalogs: List[str] = []

        # use recursion to drill down into the catalog
        if isinstance(catalog, pystac.Catalog) or isinstance(catalog, pystac.Collection):

            for child in IteratorHandler(catalog.get_children()):
                child_name = child.id
                path: str = parent_path + '/' + child_name

                # if a catalog, drill deeper
                if isinstance(child, pystac.Catalog) or isinstance(child, pystac.Collection):
                    list_of_catalog_endpoints = self.parse_catalog(
                        catalog=child,
                        parent_path=path,
                        list_of_catalog_endpoints=list_of_catalog_endpoints,
                    )
                    sub_catalogs.append(child_name)

        # if its a collection search for assets too
        if isinstance(catalog, pystac.Collection):
            self._parse_assets(
                pystac_obj=catalog,
                dataset_ids=dataset_ids,
                dataset_info_dicts=dataset_info_dicts,
            )
        elif isinstance(catalog, pystac.Catalog):
            for item in IteratorHandler(catalog.get_items()):

                self._parse_assets(
                    pystac_obj=item,
                    dataset_ids=dataset_ids,
                    dataset_info_dicts=dataset_info_dicts,
                )

        if parent_path == '':
            parent_path = '/'
        list_of_catalog_endpoints.append(
            CatalogEndpoint(
                catalog_obj=catalog,
                catalog_path=parent_path,
                dataset_ids=dataset_ids,
                sub_catalogs=sub_catalogs,
                dataset_info_dicts=dataset_info_dicts,
                contains_datasets=bool(len(dataset_ids) > 0),
            ),
        )

        return list_of_catalog_endpoints
