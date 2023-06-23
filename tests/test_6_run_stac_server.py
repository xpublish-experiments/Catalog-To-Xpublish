"""A pytest module for testing a live server using an STAC catalog."""
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
    return r'https://code.usgs.gov/wma/nhgf/stac/-/raw/main/xpublish_sample_stac/catalog/catalog.json'


@pytest.fixture(scope='session')
def app(catalog_path: Path) -> fastapi.FastAPI:
    """Return a FastAPI app instance."""
    app = catalog_to_xpublish.create_app(
        catalog_path=catalog_path,
        catalog_type='stac',
        app_name='stac_test_app',
        config_logging_dict={'log_file': 'stac_test_app.log'},
    )
    assert isinstance(app, fastapi.FastAPI)
    assert app.title == 'stac_test_app'
    assert Path(Path.cwd() / 'stac_test_app.log').exists()
    return app


@pytest.fixture(scope='session')
def client(app: fastapi.FastAPI) -> fastapi.testclient.TestClient:
    """Return a TestClient instance."""
    return fastapi.testclient.TestClient(app)


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
    assert json_dict['type'] == 'Catalog'
    assert json_dict['id'] == 'nhgf-stac-catalog'
    assert type(json_dict['links']) == list


def test_yaml_endpoint(client: fastapi.testclient.TestClient) -> None:
    """Test the YAML endpoints."""
    response = client.get('/yaml')
    assert response.status_code == 200

    yaml_dict = yaml.load(response.text, yaml.FullLoader)
    assert yaml_dict['type'] == 'Catalog'
    assert yaml_dict['id'] == 'nhgf-stac-catalog'


def test_catalog_endpoints(client: fastapi.testclient.TestClient) -> None:
    """Test the catalog endpoints."""
    response = client.get('/catalogs')
    assert response.status_code == 200

    # NOTE: this is not static as the STAC catalog is on GitLab and can change
    for catalog in ['conus404-daily', 'nhgf-stac-catalog']:
        assert catalog in response.json()

    response = client.get('/parent_catalog')
    assert response.status_code == 200
    assert response.json() == 'This is the root catalog'


def test_datasets_from_collection_endpoints(
    client: fastapi.testclient.TestClient,
) -> None:
    """Test the datasets endpoints using the STAC Collection pattern"""
    response = client.get('/conus404-daily/datasets')
    assert response.status_code == 200
    assert response.json() == ['zarr-s3']

    test_dataset_url = '/conus404-daily/datasets/zarr-s3'
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


def test_datasets_from_catalog_endpoints(
    client: fastapi.testclient.TestClient,
) -> None:
    """Test the xpublish dataset endpoints using the STAC Catalog w/ Items pattern"""
    response = client.get('/nhgf-stac-catalog/datasets')
    assert response.status_code == 200
    for dataset in [
        'GMO',
        'GMO_New',
        'PRISM',
        'PRISM_v2',
        'UofIMETDATA',
    ]:
        assert dataset in response.json()

    test_dataset_url = '/nhgf-stac-catalog/datasets/PRISM'
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
) -> None:
    """Test Xpublish Zarr metadata endpoints."""
    test_dataset_url = '/nhgf-stac-catalog/datasets/PRISM'
    response = client.get(test_dataset_url + '/zarr/.zmetadata')
    assert response.status_code == 200

    response = client.get(test_dataset_url + '/zarr/.zgroup')
    assert response.status_code == 200

    response = client.get(test_dataset_url + '/zarr/.zattrs')
    assert response.status_code == 200
