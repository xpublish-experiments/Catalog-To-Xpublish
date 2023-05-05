import intake
from pathlib import Path
from xpublish_opendap_server.catalog_search.base import (
    CatalogSearcher,
    CatalogEndpoint,
)
from typing import (
    List,
    Dict,
    Any,
    Optional,
)


class IntakeCatalogSearch(CatalogSearcher):

    def build_catalog_object(
        self,
        catalog_path: str,
    ) -> intake.Catalog:
        """Builds a catalog object."""
        catalog_path = Path(catalog_path)

        # check that the catalog path exists
        if not catalog_path.exists():
            raise FileNotFoundError(
                f'Please provide a valid intake catalog .yaml file path! '
                f'Could not find {catalog_path}'
            )
        if catalog_path.suffix != '.yaml':
            raise ValueError(
                f'Please provide a valid intake catalog .yaml file path! '
                f'File suffix must be .yaml, not {catalog_path.suffix}'
            )
        return intake.open_catalog(catalog_path)

    def parse_catalog(
        self,
        catalog: intake.Catalog,
        parent_path: Optional[str] = None,
        list_of_catalog_endpoints: Optional[List[CatalogEndpoint]] = None,
    ) -> List[CatalogEndpoint]:
        """Recursively searches a catalog for a search term."""
        if parent_path is None:
            parent_path = ''

        if list_of_catalog_endpoints is None:
            list_of_catalog_endpoints = []

        dataset_ids: List[str] = []
        dataset_info_dicts: Dict[str, Dict[str, Any]] = {}
        sub_catalogs: List[str] = []
        for child_name, child in catalog.items():
            path: str = parent_path + '/' + child_name

            # if a catalog, drill deeper recursively
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
