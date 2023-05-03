import intake
from pathlib import Path
from fastapi import (
    APIRouter,
)
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
)
from xpublish_opendap_server.catalog_classes.base import (
    CatalogSearcher,
    CatalogEndpoint,
    CatalogRouter,
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


class IntakeRouter(CatalogRouter):

    def __init__(
        self,
        catalog_endpoint_obj: CatalogEndpoint,
        prefix: Optional[str] = None,
    ) -> None:
        """
        Defines ABC:CatalogRouter methods for IntakeRouter.
        """
        # init router
        self.router = APIRouter()

        # get catalog info
        self.catalog_endpoint_obj = catalog_endpoint_obj
        self.cat_prefix = self.catalog_endpoint_obj.catalog_path
        if prefix:
            if self.cat_prefix == '/':
                self.cat_prefix = ''
        else:
            self.cat_prefix = ''

        # add all the routes
        self.router.add_api_route(
            path=f'{self.cat_prefix}/ui',
            endpoint=self.get_catalog_ui,
            methods=['GET'],
        )
        self.router.add_api_route(
            path=f'{self.cat_prefix}/catalogs',
            endpoint=self.list_sub_catalogs,
            methods=['GET'],
        )
        self.router.add_api_route(
            path=f'{self.cat_prefix}/parent_catalog',
            endpoint=self.get_parent_catalog,
            methods=['GET'],
        )
        self.router.add_api_route(
            path=f'{self.cat_prefix}/yaml',
            endpoint=self.get_catalog_as_yaml,
            methods=['GET'],
        )
        self.router.add_api_route(
            path=f'{self.cat_prefix}/json',
            endpoint=self.get_catalog_as_json,
            methods=['GET'],
        )

    def get_catalog_ui(self) -> HTMLResponse:
        """Returns the catalog ui."""
        gui = intake.interface.gui.GUI(
            [self.catalog_endpoint_obj.catalog_obj]
        )
        return HTMLResponse(
            content=gui.servable().embed(),  # .to_html(),
            status_code=200,
        )

    def list_sub_catalogs(self) -> List[str]:
        """Returns a list of sub-catalogs."""
        return self.catalog_endpoint_obj.sub_catalogs

    def get_parent_catalog(self) -> str:
        """Returns the parent catalog."""
        if self.catalog_endpoint_obj.catalog_path == '/':
            return 'This is the root catalog'
        return self.catalog_endpoint_obj.catalog_path[
            :int(self.catalog_endpoint_obj.catalog_path.rfind('/')) + 1
        ]

    def get_catalog_as_yaml(self) -> PlainTextResponse:
        """Returns the catalog yaml.

        NOTE: This may return None for some catalog types.
        """
        return PlainTextResponse(
            content=self.catalog_endpoint_obj.catalog_obj.yaml(),
            media_type='text/plain',
            status_code=200,
        )

    def get_catalog_as_json(self) -> JSONResponse:
        """Returns the catalog as JSON.

        Will be decorated with 
        NOTE: This may return None for some catalog types.
        """
        return JSONResponse(
            content='This catalog type does not support JSON serialization.',
            media_type='application/json',
            status_code=501,
        )
