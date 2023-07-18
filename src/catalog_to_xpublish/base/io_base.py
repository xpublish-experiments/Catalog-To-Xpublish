import abc
import typing
import xarray as xr


class CatalogToXarray(abc.ABC):
    """
    Abstract base class for converting a catalog object to an xarray dataset.
    """

    catalog_type: str

    @abc.abstractmethod
    def write_attributes(
        self,
        ds: xr.Dataset,
        info_dict: typing.Dict[str, typing.Any],
    ) -> xr.Dataset:
        """Write attributes from the catalog object to the dataset.attrs."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_dataset_from_catalog(
        self,
        dataset_id: str,
    ) -> xr.Dataset:
        """Get an xarray dataset from the catalog object."""
        raise NotImplementedError
