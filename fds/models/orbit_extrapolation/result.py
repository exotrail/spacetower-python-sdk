from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Sequence

from fds.client import FdsClient
from fds.models._model import RetrievableModel
from fds.models.ground_station import GroundStation
from fds.models.orbit_extrapolation.ephemeris import PowerEphemeris, KeplerianEphemeris, CartesianEphemeris, \
    PropulsionEphemeris, QuaternionEphemeris, EulerAnglesEphemeris
from fds.models.orbit_extrapolation.events import OrbitalEvent, EclipseEvent, SensorEvent, StationVisibilityEvent, \
    EventWithDuration
from fds.models.orbit_extrapolation.requests import EphemeridesRequest
from fds.models.orbital_state import OrbitalState
from fds.models.telemetry import TelemetryGpsNmea, TelemetryGpsPv, Telemetry
from fds.utils.dates import get_datetime
from fds.utils.log import log_and_raise
from spacetower_python_client import EphemerisDto


class ResultOrbitExtrapolation(RetrievableModel):
    FDS_TYPE = FdsClient.Models.RESULT_ORBIT_EXTRAPOLATION

    @dataclass
    class Ephemerides:
        power: PowerEphemeris = None
        keplerian: KeplerianEphemeris = None
        cartesian: CartesianEphemeris = None
        propulsion: PropulsionEphemeris = None
        attitude_quaternions: QuaternionEphemeris = None
        attitude_euler_angles: EulerAnglesEphemeris = None

        _name_mapping = {
            EphemeridesRequest.EphemerisType.POWER: 'power',
            EphemeridesRequest.EphemerisType.KEPLERIAN: 'keplerian',
            EphemeridesRequest.EphemerisType.CARTESIAN: 'cartesian',
            EphemeridesRequest.EphemerisType.PROPULSION: 'propulsion',
            EphemeridesRequest.EphemerisType.ATTITUDE_QUATERNIONS: 'attitude_quaternions',
            EphemeridesRequest.EphemerisType.ATTITUDE_EULER_ANGLES: 'attitude_euler_angles',
        }

        @property
        def dates(self) -> Sequence[datetime]:
            # get them from any of the ephemerides that is not None
            for ephemeris in self.__dict__.values():
                if ephemeris is not None:
                    return ephemeris.dates

        def export_ephemeris_data(self, data_name: EphemeridesRequest.EphemerisType) -> list[dict]:
            ephemeris = getattr(self, self._name_mapping[data_name])
            if ephemeris is not None:
                return ephemeris.export_table_data()
            else:
                msg = f"No {data_name} ephemeris data found."
                log_and_raise(ValueError, msg)

    def __init__(
            self,
            computed_events: list[dict] = (),
            computed_measurements: list[dict] = (),
            orbit_data_message: str = (),
            orbital_states: list[dict] = (),
            ephemerides: list[EphemerisDto] = (),
            nametag: str = None
    ):
        super().__init__(nametag)
        computed_events = self._reorder_events(computed_events)
        (self._orbital_events,
         self._eclipse_events,
         self._station_visibility_events,
         self._sensor_events) = self._group_events_into_objects(computed_events)
        self._computed_events = computed_events
        self._computed_measurements = self._create_telemetry(computed_measurements)
        self._orbit_data_message = orbit_data_message
        self._orbital_states = [OrbitalState.retrieve_by_id(os['id']) for os in
                                orbital_states]
        self._ephemerides = self._extract_ephemerides(ephemerides)

    @property
    def orbital_states(self) -> list[OrbitalState]:
        return self._orbital_states

    @property
    def ephemerides(self) -> 'ResultOrbitExtrapolation.Ephemerides':
        return self._ephemerides

    @property
    def last_orbital_state(self) -> OrbitalState | None:
        return self._orbital_states[-1] if self._orbital_states else None

    @property
    def computed_measurements(self) -> list[TelemetryGpsNmea | TelemetryGpsPv] | None:
        return self._computed_measurements if self._computed_measurements else None

    @property
    def orbital_events(self) -> list[OrbitalEvent] | None:
        return self._orbital_events if self._orbital_events else None

    @property
    def eclipse_events(self) -> list[EclipseEvent] | None:
        return self._eclipse_events if self._eclipse_events else None

    @property
    def sensor_events(self) -> list[SensorEvent] | None:
        return self._sensor_events if self._sensor_events else None

    @property
    def station_visibility_events(self) -> list[StationVisibilityEvent] | None:
        return self._station_visibility_events if self._station_visibility_events else None

    @property
    def orbit_data_message(self) -> str | None:
        return self._orbit_data_message if self._orbit_data_message else None

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'computed_events': obj_data['computedEvents'],
            'computed_measurements': obj_data['computedMeasurements'],
            'orbit_data_message': obj_data.get('orbitDataMessageOutput'),
            'orbital_states': obj_data['orbitalStates'],
            'ephemerides': obj_data.get('ephemerides'),
        }

    @staticmethod
    def _get_telemetry_from_database(computed_measurements: list[dict]) -> list[Telemetry]:
        return [Telemetry.retrieve_generic_by_id(cm['id']) for cm in computed_measurements]

    @staticmethod
    def _create_telemetry(computed_measurements: list[dict]) -> list[Telemetry]:
        telemetry = []
        for cm in computed_measurements:
            telemetry.append(Telemetry.retrieve_generic_by_id(cm['id']))
        return telemetry

    @classmethod
    def _group_events_into_objects(cls, events: list[dict]) \
            -> tuple[list[OrbitalEvent], list[EclipseEvent], list[StationVisibilityEvent], list[SensorEvent]]:
        orbital_events = []
        eclipse_events = []
        sensor_events = []
        grouped_station_events = defaultdict(list)

        for event in events:
            event_type = event.get("eventType")

            match event_type:
                case EventWithDuration.EventKind.STATION_ENTER | EventWithDuration.EventKind.STATION_EXIT:
                    ground_station_id = event.get("groundStationId")
                    utc_date = get_datetime(event.get("utcDate"))
                    grouped_station_events[ground_station_id].append((utc_date, event_type))
                case EventWithDuration.EventKind.ECLIPSE_ENTER:
                    start_date = get_datetime(event.get("utcDate"))
                    eclipse_events.append(EclipseEvent(start_date, None))
                case EventWithDuration.EventKind.ECLIPSE_EXIT:
                    end_date = get_datetime(event.get("utcDate"))
                    if len(eclipse_events) == 0:
                        eclipse_events.append(EclipseEvent(None, end_date))
                    else:
                        eclipse_events[-1].end_date = end_date
                case EventWithDuration.EventKind.SUN_IN_FOV_START:
                    start_date = get_datetime(event.get("utcDate"))
                    sensor_events.append(SensorEvent(SensorEvent.EventKind.SUN_IN_FOV,
                                                     start_date, None))
                case EventWithDuration.EventKind.SUN_IN_FOV_END:
                    end_date = get_datetime(event.get("utcDate"))
                    if len(sensor_events) == 0:
                        sensor_events.append(SensorEvent(
                            SensorEvent.EventKind.SUN_IN_FOV,
                            None, end_date))
                    else:
                        sensor_events[-1].end_date = end_date
                case _:
                    event_kind = OrbitalEvent.EventKind.from_input(event_type)
                    date = get_datetime(event.get("utcDate"))
                    orbital_events.append(OrbitalEvent(event_kind, date))

        # Finish treating the station events
        station_events = cls._group_station_visibility_events_into_objects(grouped_station_events)

        if len(orbital_events) > 0:
            orbital_events.sort(key=lambda x: x.date)
        if len(eclipse_events) > 0:
            eclipse_events.sort(
                key=lambda x: x.start_date if x.start_date is not None else datetime.min.replace(tzinfo=UTC))
        if len(sensor_events) > 0:
            sensor_events.sort(
                key=lambda x: x.start_date if x.start_date is not None else datetime.min.replace(tzinfo=UTC))

        return orbital_events, eclipse_events, station_events, sensor_events

    @classmethod
    def _group_station_visibility_events_into_objects(cls, grouped_station_events) -> list[StationVisibilityEvent]:
        station_events = []
        for ground_station_id, event_list in grouped_station_events.items():
            event_list.sort()
            start_date = None
            for date, event_type in event_list:
                if event_type == EventWithDuration.EventKind.STATION_ENTER:
                    start_date = date
                    if date == event_list[-1][0]:  # propagation ended during a station visibility
                        station_events.append(StationVisibilityEvent(
                            GroundStation.retrieve_by_id(ground_station_id),
                            start_date=start_date,
                            end_date=None
                        ))
                elif event_type == EventWithDuration.EventKind.STATION_EXIT:
                    ground_station = GroundStation.retrieve_by_id(ground_station_id)
                    station_events.append(StationVisibilityEvent(ground_station, start_date, date))

        if len(station_events) > 0:
            station_events.sort(
                key=lambda x: x.start_date if x.start_date is not None else datetime.min.replace(tzinfo=UTC))
        return station_events

    @staticmethod
    def _reorder_events(events: list[dict]) -> list[dict]:
        """Reorder events by the utcDate field."""
        return sorted(events, key=lambda x: get_datetime(x.get('utcDate')))

    @classmethod
    def _extract_ephemerides(cls, ephemerides: list[EphemerisDto]) -> 'ResultOrbitExtrapolation.Ephemerides':
        extracted_ephemerides = cls.Ephemerides()
        for ephemeris in ephemerides:
            ephemeris_type = ephemeris.get('ephemerisType')
            if ephemeris_type == 'BATTERY':
                extracted_ephemerides.power = PowerEphemeris.create_from_api_dict(dict(ephemeris))
            elif ephemeris_type == 'KEPLERIAN':
                extracted_ephemerides.keplerian = KeplerianEphemeris.create_from_api_dict(dict(ephemeris))
            elif ephemeris_type == 'CARTESIAN':
                extracted_ephemerides.cartesian = CartesianEphemeris.create_from_api_dict(dict(ephemeris))
            elif ephemeris_type == 'THRUST':
                extracted_ephemerides.propulsion = PropulsionEphemeris.create_from_api_dict(dict(ephemeris))
            elif ephemeris_type == 'QUATERNION':
                extracted_ephemerides.attitude_quaternions = QuaternionEphemeris.create_from_api_dict(dict(ephemeris))
            elif ephemeris_type == 'EULER_ANGLES':
                extracted_ephemerides.attitude_euler_angles = EulerAnglesEphemeris.create_from_api_dict(dict(ephemeris))
            else:
                msg = f"Unknown ephemeris type {ephemeris_type}."
                log_and_raise(ValueError, msg)
        return extracted_ephemerides

    def export_cartesian_ephemeris(self) -> list[dict]:
        return self.ephemerides.export_ephemeris_data(EphemeridesRequest.EphemerisType.CARTESIAN)

    def export_keplerian_ephemeris(self) -> list[dict]:
        return self.ephemerides.export_ephemeris_data(EphemeridesRequest.EphemerisType.KEPLERIAN)

    def export_power_ephemeris(self) -> list[dict]:
        return self.ephemerides.export_ephemeris_data(EphemeridesRequest.EphemerisType.POWER)

    def export_propulsion_ephemeris(self) -> list[dict]:
        return self.ephemerides.export_ephemeris_data(EphemeridesRequest.EphemerisType.PROPULSION)

    def export_quaternion_ephemeris(self) -> list[dict]:
        return self.ephemerides.export_ephemeris_data(EphemeridesRequest.EphemerisType.ATTITUDE_QUATERNIONS)

    def export_euler_angles_ephemeris(self) -> list[dict]:
        return self.ephemerides.export_ephemeris_data(EphemeridesRequest.EphemerisType.ATTITUDE_EULER_ANGLES)

    def export_event_timeline_data(self) -> list[dict]:
        """Export data for a timeline correctly sorted.

        Returns:
            list[dict]: List of dictionaries with the following keys: 'date', 'event', 'ground_station_name',
                'ground_station_id'.
        """

        columns = ['date', 'event', 'ground_station_name', 'ground_station_id']
        df_data_list = []
        for event in self._computed_events:
            event_type = event.get("eventType")
            gd_id = event.get('groundStationId', '')
            if gd_id != '':
                ground_station = GroundStation.retrieve_by_id(gd_id)
                gd_name = ground_station.name
            else:
                gd_name = ''
            df_data_list.append({columns[0]: get_datetime(event.get("utcDate")),
                                 columns[1]: event_type,
                                 columns[2]: gd_name,
                                 columns[3]: gd_id})
        return df_data_list

    def export_event_gantt_data(self) -> list[dict]:
        """Export data for Gantt chart correctly sorted.
        
        Returns:
            list[dict]: List of dictionaries with the following keys: 'start_date', 'end_date', 'event',
                'ground_station_name', 'ground_station_id', 'duration'.
        """

        columns = ['start_date', 'end_date', 'event', 'ground_station_name', 'ground_station_id', 'duration']
        df_data_list = []
        if self.station_visibility_events is not None:
            for station_event in self.station_visibility_events:
                df_data_list.append({columns[0]: station_event.start_date,
                                     columns[1]: station_event.end_date,
                                     columns[2]: 'STATION',
                                     columns[3]: station_event.ground_station.name,
                                     columns[4]: station_event.ground_station.client_id,
                                     columns[5]: station_event.duration_sec})
        if self.eclipse_events is not None:
            for eclipse_event in self.eclipse_events:
                df_data_list.append({columns[0]: eclipse_event.start_date,
                                     columns[1]: eclipse_event.end_date,
                                     columns[2]: 'ECLIPSE',
                                     columns[3]: None,
                                     columns[4]: None,
                                     columns[5]: eclipse_event.duration_sec})
        if self.orbital_events is not None:
            for orbital_event in self.orbital_events:
                df_data_list.append({columns[0]: orbital_event.date,
                                     columns[1]: orbital_event.date,
                                     columns[2]: orbital_event.kind.value,
                                     columns[3]: None,
                                     columns[4]: None,
                                     columns[5]: 0})
        if self.sensor_events is not None:
            for sensor_event in self.sensor_events:
                df_data_list.append({columns[0]: sensor_event.start_date,
                                     columns[1]: sensor_event.end_date,
                                     columns[2]: sensor_event.kind.value,
                                     columns[3]: None,
                                     columns[4]: None,
                                     columns[5]: sensor_event.duration_sec})
        if len(df_data_list) == 0:
            msg = "No events found, impossible to export data for Gantt."
            log_and_raise(ValueError, msg)

        return self.sort_event_gantt_data(columns, df_data_list)

    @staticmethod
    def sort_event_gantt_data(columns, df_data_list):
        events_data = []
        events_without_start_date = [d for d in df_data_list if d[columns[0]] is None]
        events_without_end_date = [d for d in df_data_list if d[columns[1]] is None]
        events_without_none_date = [d for d in df_data_list if d[columns[0]] is not None and d[columns[1]] is not None]
        events_without_none_date.sort(key=lambda x: x[columns[0]])

        if len(events_without_start_date) > 0:
            events_without_start_date.sort(key=lambda x: x[columns[1]])
            events_data += [ev for ev in events_without_start_date]

        events_data += events_without_none_date

        if len(events_without_end_date) > 0:
            events_without_end_date.sort(key=lambda x: x[columns[0]])
            events_data += [ev for ev in events_without_end_date]
        return events_data
