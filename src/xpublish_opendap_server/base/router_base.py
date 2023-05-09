import abc
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
from xpublish_opendap_server.base.searcher_base import (
    CatalogEndpoint,
)


class CatalogRouter(abc.ABC):
    """A router for a endpoint catalog (with or without datasets)."""

    catalog_type: str

    def __init__(
        self,
        catalog_endpoint_obj: CatalogEndpoint,
        prefix: Optional[str] = None,
    ) -> None:
        """Init is the same for all subclasses."""
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

        # add routes
        self.add_routes()

    @abc.abstractmethod
    def get_catalog_ui(self) -> HTMLResponse:
        """Returns the catalog ui.

        Will be decorated with @router.get('/')
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list_sub_catalogs(self) -> List[str]:
        """Returns a list of sub-catalogs.

        Will be decorated with @router.get('/catalogs', tags=['catalogs'])
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_parent_catalog(self) -> str:
        """Returns the parent catalog.

        Will be decorated with @router.get('/parent_catalog', tags=['parent_catalog'])
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_catalog_as_yaml(self) -> PlainTextResponse:
        """Returns the catalog yaml as plain text."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_catalog_as_json(self) -> JSONResponse:
        """Returns the catalog as JSON."""
        raise NotImplementedError

    @abc.abstractmethod
    def add_routes(self) -> None:
        """Adds routes to the APIRouter object."""
        raise NotImplementedError
