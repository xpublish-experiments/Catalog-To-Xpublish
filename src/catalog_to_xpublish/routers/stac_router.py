import json
import yaml
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
)
from typing import (
    List,
    Optional,
)
from xpublish_opendap_server.base import (
    CatalogEndpoint,
)
from xpublish_opendap_server.base import (
    CatalogRouter,
)
from xpublish_opendap_server.factory import (
    CatalogRouterClass,
)


@CatalogRouterClass
class STACRouter(CatalogRouter):
    """A router for a STAC endpoint catalog (with or without datasets)."""

    catalog_type: str = 'stac'

    def __init__(
        self,
        catalog_endpoint_obj: CatalogEndpoint,
        prefix: Optional[str] = None,
    ) -> None:
        """Init the class using the CatalogRouter ABC."""
        super().__init__(
            catalog_endpoint_obj=catalog_endpoint_obj,
            prefix=prefix,
        )

    def get_catalog_ui(self) -> HTMLResponse:
        """Returns the catalog ui.

        Will be decorated with @router.get('/')
        """
        # TODO: https://panel.holoviz.org/user_guide/FastAPI.html
        raise NotImplementedError

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
        """Returns the catalog yaml as plain text."""
        return PlainTextResponse(
            content=yaml.dump(self.catalog_endpoint_obj.catalog_obj.to_dict()),
            media_type='text/plain',
            status_code=200,
        )

    def get_catalog_as_json(self) -> JSONResponse:
        """Returns the catalog as JSON."""
        return JSONResponse(
            content=json.dumps(
                self.catalog_endpoint_obj.catalog_obj.to_dict()),
            media_type='application/json',
            status_code=200,
        )

    def add_routes(self) -> None:
        """Adds routes to the router."""
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
