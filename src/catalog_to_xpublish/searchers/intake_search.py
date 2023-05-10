import intake
from pathlib import Path
from catalog_to_xpublish.base import (
    CatalogSearcher,
    CatalogEndpoint,
)
from catalog_to_xpublish.factory import (
    CatalogSearcherClass,
)
from typing import (
    List,
    Dict,
    Any,
    Optional,
)


@CatalogSearcherClass
class IntakeCatalogSearch(CatalogSearcher):
    """Intake Catalog searcher."""
    catalog_type: str = 'intake'

    def __init__(
        self,
        catalog_path: Path | str,
        suffixes: Optional[List[str]] = None,
    ) -> None:
        """Initializes the catalog searcher."""

        self.__catalog_path: Path = catalog_path
        self.__suffixes: List[str] = suffixes
        self.__catalog_obj: intake.Catalog = None

    @property
    def catalog_path(self) -> Path:
        if isinstance(self.__catalog_path, str):
            self.__catalog_path = Path(self.__catalog_path)
        if not isinstance(self.__catalog_path, Path):
            raise TypeError(
                f'Please provide a valid intake catalog .yaml file path! '
                f'Expected a str or Path, got {type(self.__catalog_path)}'
            )
        if not self.__catalog_path.exists():
            raise FileNotFoundError(
                f'Please provide a valid intake catalog .yaml file path! '
                f'Could not find {self.__catalog_path}'
            )
        if self.__catalog_path.suffix != '.yaml':
            raise ValueError(
                f'Please provide a valid intake catalog .yaml file path! '
                f'File suffix must be .yaml, not {self.__catalog_path.suffix}'
            )
        return self.__catalog_path

    @property
    def suffixes(self) -> List[str]:
        if self.__suffixes is None:
            # TODO: test with NetCDF files
            self.__suffixes = [
                # '.nc',
                '.zarr',
            ]
        return self.__suffixes

    @property
    def catalog_object(self) -> intake.Catalog:
        """Builds/returns a catalog object (ex: intake.Catalog)."""
        if self.__catalog_obj is None:
            self.__catalog_obj = intake.open_catalog(self.catalog_path)
        return self.__catalog_obj

    def parse_catalog(
        self,
        catalog: Optional[intake.Catalog] = None,
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
        for child_name, child in catalog.items():
            path: str = parent_path + '/' + child_name

            # if a catalog, drill deeper
            if isinstance(child, intake.catalog.Catalog):
                list_of_catalog_endpoints = self.parse_catalog(
                    catalog=child,
                    parent_path=path,
                    list_of_catalog_endpoints=list_of_catalog_endpoints,
                )
                sub_catalogs.append(child_name)

            # if the catalog contains a data source, make it a valid get dataset router
            elif isinstance(child, intake.source.base.DataSource):
                dataset_ids.append(child_name)
                dataset_info_dicts[child_name] = child.describe()

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
            )
        )

        return list_of_catalog_endpoints
