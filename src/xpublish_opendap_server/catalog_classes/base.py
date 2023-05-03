import abc
from pydantic import BaseModel
from fastapi import (
    APIRouter,
)
from fastapi.responses import (
    HTMLResponse,
    FileResponse,
    JSONResponse,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)


class CatalogEndpoint(BaseModel):
    """A catalog level containing datasets.

    Attributes:
        catalog_obj: it's type will match CatalogSearcher.build_catalog_object() output.
        catalog_path: The path to the catalog delineated by /.
            For example, 'catalog1/catalog2/catalog3'.
            This will be used for the plugin prefix.
        dataset_ids: A list of dataset ids.
        dataset_info_dicts: A dictionary of dataset info dictionaries.
            This is used to provide additional access information.
    """
    catalog_obj: object
    catalog_path: str
    dataset_ids: List[str]
    dataset_info_dicts: Dict[str, Dict[str, Any]]
    contains_datasets: bool


class CatalogSearcher(abc.ABC):

    suffixes: List[str] = [
        '.nc',
        '.zarr',
    ]

    @abc.abstractmethod
    def build_catalog_object(
        self,
        catalog_path: str,
    ) -> object:
        """Builds a catalog object (ex: intake.Catalog).

        NOTE: The exact object type will depend on the catalog type.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def parse_catalog(
        self,
        catalog: object,
        parent_path: Optional[str] = None,
        list_of_catalog_endpoints: Optional[List[CatalogEndpoint]] = None,
    ) -> List[CatalogEndpoint]:
        """Recursively searches a catalog for a search term."""
        raise NotImplementedError


class CatalogRouter(abc.ABC):
    """A router for a endpoint catalog (with or without datasets)."""

    # router: APIRouter
    # catalog_endpoint_obj: CatalogEndpoint

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
    def get_catalog_as_yaml(self) -> FileResponse:
        """Returns the catalog yaml.

        Will be decorated with @router.get('.yaml', tags=['.yaml'])
        NOTE: This may return None for some catalog types.
        """
        # FileResponse(content=yaml_data, media_type="application/x-yaml")
        raise NotImplementedError

    @abc.abstractmethod
    def get_catalog_as_json(self) -> JSONResponse:
        """Returns the catalog as JSON.

        Will be decorated with @router.get('.json', tags=['.json'])
        NOTE: This may return None for some catalog types.
        """
        raise NotImplementedError


class BaseRouter:

    def __init__(
        self,
        prefix: Optional[str] = None,
    ) -> None:
        if prefix == '/':
            prefix = ''
        self.router = APIRouter(prefix=prefix)
