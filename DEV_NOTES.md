Xavier's Development Notes
===========================
* Following instructions / formatting shown here: https://fastapi.tiangolo.com/tutorial/bigger-applications/

**ROUTERS**
* So the opendap router as it exists is built on the basic xpublish set up where the dataset is already loaded and required the `opendap` prefix.
* One option is to build "Dataset Provider Plugin" (see docs) uses the URL to get to the correct catalog position, then uses our existing catalog function. These routers take priority apparently, but we should test it out.
    * The issue is you need to define a function with a list of datasets it knows about a-priori.
    * BOOM: What if we init these plugins when we fire up the server, and have them references by catalog position as the prefix!!! Therefore each specific provider plugin could know what it has to offer.
    * Yes this is the way. When we use the recursion we don't actually make a router, we instead get a chain of catalog hierarchy and a prefix (catalog hierarchy). Ideally we have the catalog object cached from the get-go, so when the prefix is triggered the correct router is used.
    * FACTORY? -> we need a way to make these construct these classes as we go?

## STAC + Intake
* OKAY BIG SWITCH UP. We want a router that maps out the hierachy of both STAC and Intake catalogs.
* We then want to pass the final catalog level to a catalog specific implementation of `CatalogToXarray`.
    * Figuring our how to do this may take some trial and error, but would be pretty darn lit.
    * Potentially follow this convention for STAC: https://github.com/stac-extensions/storage (and write in docs).
    * Start with intake.

## Components
* For `xpublish_opendap` we need data in `xarray.Dataset`, therefore we will have `fsspec` functions to open the zarr files.
* For `xpublish` we either need all served datasets opened, or find a way around that where they can be accessed as needed (ideal) and cached. This is very important to figure out.


## [`fsspec`](https://filesystem-spec.readthedocs.io/en/latest/index.html)
* One can open local, s3 bucket, or HTTPs files using the `fsspec.FileSystem` constructor. Therefore regardless of where the catalog we use points too, we can read and stream out the data.
* Later on we could use [`fsspec`'s Async capabilities](https://filesystem-spec.readthedocs.io/en/latest/async.html) to open and stream multiple datasets at the same time.

## [`opendap_protocol`](https://github.com/MeteoSwiss/opendap-protocol)
* The main objects are `DAPObject` which is inherited by `DAPAtom`, `Dataset`, and `Sequence`, and `Attribute`.
* `Grid` and `Array`inherit from an intermediary class `DAPDataObject`(that inherits from `DAPObject`) and basically allows constraints to be sliced.
* `DAPObject` functions are often generators that yield byte encoded data if the constraint string is valid (`meets_constrain()`).
* All datatypes are classes that inherit from `DAPAtom` (i.e., `opendap_protocol.Int32`).



## [`xpublish_opendap`](https://github.com/xpublish-community/xpublish-opendap)
Has two components: `dap_xarray.py` which adapts `xarray` objects to `opendap_protocol` objects, and `plugin.py` which inherits from the `xpublish.Plugin` class and routes URLs with "opendap" in them to the appropriate functions.

### `dap_xarray.py`
* `dap_dtype()` returns a `opendap_protocol` datatype for a given numpy/xarray datatype.
* The main `dap_dataset()` function returns a `opendap_protocol.Dataset` object from an `xarray.Dataset` and a dataset name. This involves mapping the dimensions -> `opendap_protocol.Array`s, grid values to `opendap_protocol.Grid`, and attributes dictionary `opendap_protocol.Attribute`.
* Note that the dimensions are mapped after CF encoding them. Attributes are then written on to each dimension.

### `plugin.py`
* Uses `fastapi.Depends` to control type hinting / dependency injection. The dependencies themselves are pulled from the [xpublish.plugins module](https://github.com/xpublish-community/xpublish/blob/main/xpublish/plugins/hooks.py#L18). This uses [`pydantic.Field` under-the-hood](https://fastapi.tiangolo.com/tutorial/body-fields/) which keeps track of metadata / what each argument means semantically.
* Handles cacheing with `cachey.Cache`. If a dataset is cached it is returned, otherwise `dap_xarray.dap_dataset()` is called.
* Basically a prefix and/or a tag (in this case "opendap") triggers the `fastapi.APIRouter`.
* For GET calls, constraints are parsed from the URL, the `opendap_protocol.Dataset` object is passed in (or generated), and functions are called appropriately. For example `opendap_protocol.DAPDataset.dds(constraints: str = constraints)`.
