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
from catalog_to_xpublish.base import (
    CatalogEndpoint,
)
from catalog_to_xpublish.base import (
    CatalogRouter,
)
from catalog_to_xpublish.factory import (
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
            content=yaml.dump(
                json.loads(
                    json.dumps(
                        self.catalog_endpoint_obj.catalog_obj.to_dict(),
                    ),
                ),
            ),
            media_type='text/plain',
            status_code=200,
        )

    def get_catalog_as_json(self) -> JSONResponse:
        """Returns the catalog as JSON."""
        return JSONResponse(
            content=self.catalog_endpoint_obj.catalog_obj.to_dict(),
            media_type='application/json',
            status_code=200,
        )

    def add_routes(self) -> None:
        """Adds routes to the router."""

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
