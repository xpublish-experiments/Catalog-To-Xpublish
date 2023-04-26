Xavier's Development Notes
===========================
## `fsspec`

## `opendap_protocol`
* `Attribute`
## `xpublish_opendap`
Has two components: `dap_xarray.py` which adapts `xarray` objects to `opendap_protocol` objects, and `plugin.py` which inherits from the `xpublish.Plugin` class and routes URLs with "opendap" in them to the appropriate functions.
### `dap_xarray.py`
* `dap_dtype()` returns a `opendap_protocol` datatype for a given numpy/xarray datatype.
* 

### `plugin.py`
* Uses `fastapi.Depends` to control type hinting / dependency injection. The dependencies themselves are pulled from the [xpublish.plugins module](https://github.com/xpublish-community/xpublish/blob/main/xpublish/plugins/hooks.py#L18). This uses [`pydantic.Field` under-the-hood](https://fastapi.tiangolo.com/tutorial/body-fields/) which keeps track of metadata / what each argument means semantically.
* Handles cacheing with `cachey.Cache`.
* Basically a prefix and/or a tag (in this case "opendap") triggers the `fastapi.APIRouter`.