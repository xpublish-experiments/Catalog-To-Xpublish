"""Main server file"""
import uvicorn
from pathlib import Path
from catalog_to_xpublish.server_functions import create_app

# CATALOG_TYPE: str = 'intake'  # or 'stac'
# CATALOG_PATH = Path.cwd() / 'test_catalogs' / 'test_intake_zarr_catalog.yaml'

CATALOG_TYPE: str = 'stac'
CATALOG_PATH = Path.cwd() / 'test_catalogs' / 'test_stac_zarr_catalog.json'

APP_NAME = 'Xpublish Server'

# add plugins here
XPUBLISH_PLUGINS = []
try:
    from xpublish_opendap import OpenDapPlugin
    XPUBLISH_PLUGINS.append(OpenDapPlugin)
except ImportError:
    print('xpublish_opendap not installed. Skipping OpenDAP plugin.')


LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8000


app = create_app(
    catalog_path=CATALOG_PATH,
    catalog_type=CATALOG_TYPE,
    app_name=APP_NAME,
    xpublish_plugins=XPUBLISH_PLUGINS,
)


def main() -> None:
    """Main function to run the server."""
    uvicorn.run(
        'run_server:app',
        host=LOCAL_HOST,
        port=LOCAL_PORT,
        reload=True,
    )


if __name__ == '__main__':
    main()
