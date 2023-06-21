"""A pytest module for testing a live server using an Intake catalog."""
import catalog_to_xpublish
import pytest
import fastapi
import json
import yaml
from fastapi.testclient import TestClient
from pathlib import Path


@pytest.fixture(scope='session')
def catalog_path() -> Path:
    """Returns the path to the test catalog."""
    if Path.cwd().name == 'Catalog-To-Xpublish':
        home_dir = Path.cwd()
    elif Path.cwd().name == 'tests':
        home_dir = Path.cwd().parent
    else:
        raise FileNotFoundError(
            f'Please run this test from the root directory of the repository.',
            f'CWD={Path.cwd()}',
        )
    return home_dir / 'test_catalogs' / \
        'test_intake_zarr_catalog.yaml'


@pytest.fixture(scope='session')
def app(catalog_path: Path) -> fastapi.FastAPI:
    """Return a FastAPI app instance."""
    app = catalog_to_xpublish.create_app(
        catalog_path=catalog_path,
        catalog_type='intake',
        app_name='intake_test_app',
        config_logging_dict={'log_file': 'intake_test_app.log'},
    )

    # check that things are in place
    assert isinstance(app, fastapi.FastAPI)
    assert app.title == 'intake_test_app'
    assert Path(Path.cwd() / 'intake_test_app.log').exists()
    return app


@pytest.fixture(scope='session')
def client(app: fastapi.FastAPI) -> fastapi.testclient.TestClient:
    """Return a TestClient instance."""
    return fastapi.testclient.TestClient(app)


@pytest.fixture(scope='session')
def test_dataset_url() -> str:
    """Return the URL of a dataset."""
    return '/s3_catalog/datasets/alaska-et-2020-subset-s3'


def test_docs(client: fastapi.testclient.TestClient) -> None:
    """Test the docs."""
    # test swagger docs
    response = client.get('/docs')
    assert response.status_code == 200

    # test redoc docs
    response = client.get('/redoc')
    assert response.status_code == 200

    # test openapi.json
    response = client.get('/openapi.json')
    assert response.status_code == 200


def test_json_endpoint(client: fastapi.testclient.TestClient) -> None:
    """Test the JSON endpoints."""
    response = client.get('/json')
    assert response.status_code == 200

    json_dict = json.loads(response.json())
    assert list(json_dict['sources'].keys())[0] == 'test_intake_zarr_catalog'


def test_yaml_endpoint(client: fastapi.testclient.TestClient) -> None:
    """Test the YAML endpoints."""
    response = client.get('/yaml')
    assert response.status_code == 200

    yaml_dict = yaml.load(response.text, yaml.FullLoader)
    assert list(yaml_dict['sources'].keys())[0] == 'test_intake_zarr_catalog'


def test_catalog_endpoints(client: fastapi.testclient.TestClient) -> None:
    """Test the catalog endpoints."""
    response = client.get('/catalogs')
    assert response.status_code == 200
    assert response.json() == ['s3_catalog', 'osn_catalog']

    response = client.get('/parent_catalog')
    assert response.status_code == 200
    assert response.json() == 'This is the root catalog'


def test_datasets_endpoints(
    client: fastapi.testclient.TestClient,
    test_dataset_url: str,
) -> None:
    """Test the datasets endpoints."""
    response = client.get('/s3_catalog/datasets')
    assert response.status_code == 200
    assert response.json() == [
        'alaska-et-2020-subset-s3',
        'red-river-subset-s3',
        'conus404-hourly-s3',
        'era5-2019-may-precip-s3',
    ]

    # test the xpublish endpoints
    response = client.get(test_dataset_url)
    assert response.status_code == 200

    response = client.get(test_dataset_url + '/keys')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

    response = client.get(test_dataset_url + '/info')
    assert response.status_code == 200
    json_dict = response.json()
    assert 'dimensions' in json_dict.keys()
    assert 'variables' in json_dict.keys()


def test_zarr_endpoints(
    client: fastapi.testclient.TestClient,
    test_dataset_url: str,
) -> None:
    """Test Xpublish Zarr metadata endpoints."""
    response = client.get(test_dataset_url + '/zarr/.zmetadata')
    assert response.status_code == 200

    response = client.get(test_dataset_url + '/zarr/.zgroup')
    assert response.status_code == 200

    response = client.get(test_dataset_url + '/zarr/.zattrs')
    assert response.status_code == 200
