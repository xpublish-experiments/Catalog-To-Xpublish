import dataclasses
import xpublish
from xpublish_opendap_server.catalog_search import (
    CatalogEndpoint,
    CatalogSearcher,
    IntakeCatalogSearch,
    STACCatalogSearch,
    DatasetProviderPlugin,
)
from xpublish_opendap_server.io_classes import (
    CatalogToXarray,
    IntakeToXarray,
    STACToXarray,
)
from xpublish_opendap_server.routers import (
    CatalogRouter,
    IntakeRouter,
    STACRouter,
)
from pathlib import Path
from typing import (
    List,
    Dict,
    Optional,
)

# TODO: this could be a factory style implementation?


@dataclasses.dataclass
class CatalogImplementation:
    """A class to hold the different catalog implementation classes."""
    catalog_search: CatalogSearcher
    catalog_to_xarray: CatalogToXarray
    catalog_router: CatalogRouter


@dataclasses.dataclass
class AppComponents:
    """A class to hold the different inputs for launching our server app."""
    catalog_path: Path
    catalog_name: str
    catalog_implementation: CatalogImplementation
    name: str
    xpublish_plugins: list


CatalogImplementations: Dict[str, CatalogImplementation] = {
    'intake': CatalogImplementation(
        catalog_search=IntakeCatalogSearch,
        catalog_to_xarray=IntakeToXarray,
        catalog_router=IntakeRouter,
    ),
    'stac': CatalogImplementation(
        catalog_search=STACCatalogSearch,
        catalog_to_xarray=STACToXarray,
        catalog_router=STACRouter,
    ),
}


def validate_arguments(
    catalog_path: Path,
    catalog_type: str,
    app_name: Optional[str] = None,
    xpublish_plugins: Optional[List[xpublish.Plugin]] = None,
) -> AppComponents:
    """Validates the arguments passed to the create_app function."""
    # check catalog path argument and get name
    if not isinstance(catalog_path, Path):
        raise TypeError(
            f'catalog_path must be a Path object, not {type(catalog_path)}'
        )
    if not catalog_path.exists():
        raise FileNotFoundError(
            f'catalog_path={catalog_path} does not exist.'
        )

    catalog_name: str = catalog_path.name.replace(catalog_path.suffix, '')

    # check catalog type argument
    if not isinstance(catalog_type, str):
        raise TypeError(
            f'catalog_type must be a str, not {type(catalog_type)}'
        )
    catalog_type = catalog_type.lower()
    if not catalog_type in CatalogImplementations.keys():
        raise KeyError(
            f'catalog_type={catalog_type} is not in {CatalogImplementations.keys()}.'
        )
    catalog_implementation = CatalogImplementations[catalog_type]

    # check app name argument
    if not app_name:
        app_name = 'Catalog_Xpublish_Server'
    elif not isinstance(app_name, str):
        raise TypeError(
            f'app_name must be a str, not {type(app_name)}'
        )

    # check plugins list argument
    if not xpublish_plugins:
        xpublish_plugins = []
    if not isinstance(xpublish_plugins, list):
        raise TypeError(
            f'xpublish_plugins must be a list of xpublish.Plugin objects, not {type(xpublish_plugins)}'
        )

    return AppComponents(
        catalog_path=catalog_path,
        catalog_name=catalog_name,
        catalog_implementation=catalog_implementation,
        name=app_name,
        xpublish_plugins=xpublish_plugins,
    )
