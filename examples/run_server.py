"""Main server file"""
import uvicorn
import warnings
from pathlib import Path
from catalog_to_xpublish.server_functions import create_app
from catalog_to_xpublish.log import LoggingConfigDict

CATALOG_TYPE: str = 'stac'  # or 'stac'

if CATALOG_TYPE == 'intake':
    if Path.cwd().name == 'examples':
        root_path = Path.cwd().parent
    elif Path.cwd().name == 'Catalog-To-Xpublish':
        root_path = Path.cwd()

    CATALOG_PATH = Path.cwd() / 'test_catalogs' / 'test_intake_zarr_catalog.yaml'
elif CATALOG_TYPE == 'stac':
    CATALOG_PATH = r'https://code.usgs.gov/wma/nhgf/stac/-/raw/main/xpublish_sample_stac/catalog/catalog.json'
else:
    raise ValueError(
        f'Invalid catalog type: {CATALOG_TYPE}. Must be "intake" or "stac".'
    )

APP_NAME: str = f'Xpublish Server (from {CATALOG_TYPE})'

# add plugins here
XPUBLISH_PLUGINS = []
try:
    from xpublish_opendap import OpenDapPlugin
    XPUBLISH_PLUGINS.append(OpenDapPlugin)
except ImportError:
    warnings.warn('xpublish_opendap not installed. Skipping OpenDAP plugin.')


LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8000

# config logging
CONFIG_LOGGING_DICT: LoggingConfigDict = {
    'level': 'INFO',
    'log_file': 'xpublish_server.log',
}

app = create_app(
    catalog_path=CATALOG_PATH,
    catalog_type=CATALOG_TYPE,
    app_name=APP_NAME,
    xpublish_plugins=XPUBLISH_PLUGINS,
    config_logging_dict=CONFIG_LOGGING_DICT,
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
