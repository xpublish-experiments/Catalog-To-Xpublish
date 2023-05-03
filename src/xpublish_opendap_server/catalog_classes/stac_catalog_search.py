from pystac_client import Client
from xpublish_opendap_server.catalog_classes.base import (
    CatalogSearcher,
    CatalogEndpoint,
)
from typing import (
    List,
    Dict,
    Optional,
)

# TODO: Make a test STAC catalog and get this to work


class STACCatalogSearch(CatalogSearcher):

    def build_catalog_object(
        self,
        catalog_path: str,
    ) -> Client:
        """Builds a catalog object."""
        return Client.open(catalog_path)

    def parse_catalog(
        self,
        catalog: Client,
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
        for child_name, child in catalog.items():
            path: str = parent_path + '/' + child_name

            # if a catalog, drill deeper recursively
            if child.assets:
                list_of_catalog_endpoints = self.parse_catalog(
                    catalog=child,
                    parent_path=path,
                    list_of_catalog_endpoints=list_of_catalog_endpoints,
                )

            # if the catalog contains a data source, make it a valid get dataset router
            elif child.items:
                dataset_ids.append(child_name)
                dataset_info_dicts[child_name] = child.describe()

        if len(dataset_ids) > 0:
            if parent_path == '':
                parent_path = '/'
            list_of_catalog_endpoints.append(
                CatalogEndpoint(
                    catalog_obj=catalog,
                    catalog_path=parent_path,
                    dataset_ids=dataset_ids,
                    dataset_info_dicts=dataset_info_dicts,
                )
            )

        return list_of_catalog_endpoints

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
