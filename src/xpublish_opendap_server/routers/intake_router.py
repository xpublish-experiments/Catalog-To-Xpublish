from fastapi import (
    APIRouter,
)
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
)
from typing import (
    List,
    Optional,
)
from xpublish_opendap_server.catalog_search.base import (
    CatalogEndpoint,
)
from xpublish_opendap_server.routers.base import (
    CatalogRouter,
)


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
