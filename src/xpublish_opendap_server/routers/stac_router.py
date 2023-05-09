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
        """Returns a list of sub-catalogs.

        Will be decorated with @router.get('/catalogs', tags=['catalogs'])
        """
        raise NotImplementedError

    def get_parent_catalog(self) -> str:
        """Returns the parent catalog.

        Will be decorated with @router.get('/parent_catalog', tags=['parent_catalog'])
        """
        raise NotImplementedError

    def get_catalog_as_yaml(self) -> PlainTextResponse:
        """Returns the catalog yaml as plain text."""
        raise NotImplementedError

    def get_catalog_as_json(self) -> JSONResponse:
        """Returns the catalog as JSON."""
        raise NotImplementedError
