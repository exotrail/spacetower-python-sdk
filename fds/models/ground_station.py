from dataclasses import dataclass, astuple
from typing import Sequence

from fds.client import FdsClient
from fds.models._model import RetrievableModel


class GroundStation(RetrievableModel):
    FDS_TYPE = FdsClient.Models.GROUND_STATION

    @dataclass
    class ElevationMask:
        azimuth: float
        elevation: float

    @dataclass
    class Coordinates:
        latitude: float
        longitude: float

    def __init__(
            self,
            name: str,
            latitude: float,
            longitude: float,
            altitude: float,
            min_elevation: float = None,
            elevation_masks: Sequence[tuple[float, float]] = None,
            nametag: str = None
    ):
        """
        Args:
            name (str): Name of the ground station.
            latitude (float): (Unit: deg)
            longitude (float): (Unit: deg)
            altitude (float): (Unit: km)
            min_elevation (float, optional): (Unit: deg)
            elevation_masks (Sequence[list(float, float)], optional): list of azimuth-elevation pairs (Unit: deg)
        """
        super().__init__(nametag)
        self._name = name
        self._coordinates = self.Coordinates(latitude, longitude)
        self._altitude = altitude
        self._min_elevation = min_elevation
        self._elevation_masks = [self.ElevationMask(*elevation_mask) for
                                 elevation_mask in
                                 elevation_masks] if elevation_masks is not None else None

    @property
    def name(self) -> str:
        return self._name

    @property
    def coordinates(self) -> Coordinates:
        return self._coordinates

    @property
    def altitude(self) -> float:
        return self._altitude

    @property
    def min_elevation(self) -> float:
        return self._min_elevation

    @property
    def elevation_masks(self) -> Sequence[ElevationMask]:
        return self._elevation_masks

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {'name': obj_data['name'],
                'latitude': obj_data['latitude'],
                'longitude': obj_data['longitude'],
                'altitude': obj_data['altitude'],
                'min_elevation': obj_data['minElevation'],
                'elevation_masks': obj_data.get('elevationMask'),
                }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'name': self.name,
                'latitude': self.coordinates.latitude,
                'longitude': self.coordinates.longitude,
                'altitude': self.altitude,
                'minElevation': self.min_elevation,
                'elevationMask': [astuple(em) for em in
                                  self.elevation_masks] if self.elevation_masks is not None else None
            }
        )
        return d
