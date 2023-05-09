"""Init file for catalog routers (and any others)."""
from xpublish_opendap_server.routers.base import (
    CatalogRouter,
)
from xpublish_opendap_server.routers.intake_router import (
    IntakeCatalogRouter,
)
from xpublish_opendap_server.routers.stac_router import (
    STACCatalogRouter,
)
