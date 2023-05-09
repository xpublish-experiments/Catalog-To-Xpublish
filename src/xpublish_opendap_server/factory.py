"""
A factory for creating and validating catalog implementations (i.e., STAC, Intake, etc.).
"""
import dataclasses
from xpublish_opendap_server.base import (
    CatalogSearcher,
    CatalogToXarray,
    CatalogRouter,
)
from typing import (
    List,
    Dict,
)


@dataclasses.dataclass
class CatalogImplementation:
    """A class to hold the different catalog implementation classes."""
    catalog_search: CatalogSearcher
    catalog_to_xarray: CatalogToXarray
    catalog_router: CatalogRouter


class CatalogSearcherClass:
    def __init__(
        cls,
        args,
    ) -> None:
        """Initializes a catalog searcher."""
        if not issubclass(args, CatalogSearcher):
            raise TypeError(
                f'Please provide a valid catalog searcher! '
                f'Expected a subclass of CatalogSearcher, got {type(args)}'
            )
        CatalogImplementationFactory.register_searcher(args)


class CatalogIOClass:
    def __init__(
        cls,
        args,
    ) -> None:
        """Initializes a catalog IO Class."""
        if not issubclass(args, CatalogToXarray):
            raise TypeError(
                f'Please provide a valid catalog IO class! '
                f'Expected a subclass of CatalogToXarray, got {type(args)}'
            )
        CatalogImplementationFactory.register_io(args)


class CatalogRouterClass:
    def __init__(
        cls,
        args,
    ) -> None:
        """Initializes a catalog router."""
        if not issubclass(args, CatalogRouter):
            raise TypeError(
                f'Please provide a valid catalog router! '
                f'Expected a subclass of CatalogRouter, got {type(args)}'
            )
        CatalogImplementationFactory.register_router(args)


class CatalogImplementationFactory:

    __catalog_searchers: Dict[str, CatalogSearcher] = {}
    __catalog_io_classes: Dict[str, CatalogToXarray] = {}
    __catalog_routers: Dict[str, CatalogRouter] = {}
    __catalog_type_keys: List[str] = []
    __catalog_implementations: Dict[str, CatalogImplementation] = {}

    @classmethod
    def register_searcher(
        cls,
        catalog_searcher: CatalogSearcher,
    ) -> None:
        cls.__catalog_searchers[
            catalog_searcher.catalog_type
        ] = catalog_searcher

    @classmethod
    def register_io(
        cls,
        catalog_io_class: CatalogToXarray,
    ) -> None:
        cls.__catalog_io_classes[
            catalog_io_class.catalog_type
        ] = catalog_io_class

    @classmethod
    def register_router(
        cls,
        catalog_router: CatalogRouter,
    ) -> None:
        cls.__catalog_routers[
            catalog_router.catalog_type
        ] = catalog_router

    @classmethod
    def _get_catalog_dicts(
        cls,
    ) -> List[Dict[str, CatalogSearcher | CatalogToXarray | CatalogRouter]]:
        """Returns a list of all catalog classes."""
        return [
            cls.__catalog_searchers,
            cls.__catalog_io_classes,
            cls.__catalog_routers,
        ]

    @classmethod
    def __get_catalog_type_keys(
        cls,
    ) -> List[str]:
        """Returns a list of all catalog types."""
        catalog_dicts = cls._get_catalog_dicts()
        if catalog_dicts == [{}, {}, {}]:
            raise ValueError(
                f'No catalog implementations have been registered! '
            )

        # make sure there are no partial implementations
        if len(cls.__catalog_type_keys) == 0:

            for i, catalog_dict in enumerate(catalog_dicts):
                if i == 0:
                    all_keys = list(set(catalog_dict.keys()))
                else:
                    more_keys = set(
                        all_keys.copy() + list(catalog_dict.keys())
                    )
                    if len(more_keys) != len(all_keys):
                        raise ValueError(
                            f'Found a partial implementation of a catalog type! '
                            f'There must a a valid CatalogSearcher, CatalogToXarray, and CatalogRouter '
                            f'for each catalog type. '
                        )
                    else:
                        all_keys = list(more_keys)
            cls.__catalog_type_keys = all_keys
        return cls.__catalog_type_keys

    @classmethod
    def get_all_implementations(
        cls,
    ) -> Dict[str, CatalogImplementation]:
        """Returns a dictionary of valid catalog type implementations."""
        catalog_keys = cls.__get_catalog_type_keys()
        if len(cls.__catalog_implementations) != len(catalog_keys):
            for catalog_type in cls.__get_catalog_type_keys():
                cls.__catalog_implementations[catalog_type] = CatalogImplementation(
                    catalog_search=cls.__catalog_searchers[catalog_type],
                    catalog_to_xarray=cls.__catalog_io_classes[catalog_type],
                    catalog_router=cls.__catalog_routers[catalog_type],
                )
        return cls.__catalog_implementations

    @classmethod
    def get_catalog_implementation(
        cls,
        catalog_type: str,
    ) -> CatalogImplementation:
        return cls.get_all_implementations()[catalog_type]
