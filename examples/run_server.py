"""Main server file"""
import uvicorn
import warnings
from pathlib import Path
from catalog_to_xpublish.server_functions import create_app
from catalog_to_xpublish.log import LoggingConfigDict

# DEFINE INPUTS BELOW
CATALOG_TYPE: str = 'intake'  # 'stac' or 'intake'
APP_NAME: str = f'Xpublish Server (from {CATALOG_TYPE})'
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8000

# add plugins here
XPUBLISH_PLUGINS = []
try:
    from xpublish_opendap import OpenDapPlugin
    XPUBLISH_PLUGINS.append(OpenDapPlugin)
except ImportError:
    warnings.warn('xpublish_opendap not installed. Skipping OpenDAP plugin.')

# config logging
CONFIG_LOGGING_DICT: LoggingConfigDict = {
    'level': 'INFO',
    'log_file': 'xpublish_server.log',
}


# find example catalog
if Path.cwd().name == 'examples':
    root_path = Path.cwd().parent
elif Path.cwd().name == 'Catalog-To-Xpublish':
    root_path = Path.cwd()
else:
    raise FileNotFoundError(
        f'Please run this script from the root directory of the repository '
        f'or /examples. CWD={Path.cwd()}',
    )

if CATALOG_TYPE == 'intake':
    catalog_path = root_path / 'test_catalogs' / 'test_intake_zarr_catalog.yaml'
elif CATALOG_TYPE == 'stac':
    catalog_path = root_path / 'test_catalogs' / \
        'sample_stac_catalog' / 'catalog.json'
else:
    raise ValueError(
        f'Invalid catalog type: {CATALOG_TYPE}. Must be "intake" or "stac".',
    )

# create app
app = create_app(
    catalog_path=catalog_path,
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
