"""Pydantic models for race metadata.json validation."""

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, field_validator


class RaceMetadata(BaseModel):
    name: str
    date: str
    distance_value: Optional[float] = None
    distance_unit: str
    type: str
    surface: str
    course_style: str
    start_city: str
    start_state: str
    end_state: str
    personal_states_covered: list[str] = []
    location_gps: Optional[list[float]] = None


class Results(BaseModel):
    official_time: str
    elevation_gain: Optional[float] = None
    elevation_loss: Optional[float] = None
    elevation_unit: str = "feet"
    status: str = ""
    is_official: bool = True
    is_sanctioned: bool = True
    team_name: str = ""
    personal_legs: list[Union[str, int]] = []
    notes: str = ""


class Weather(BaseModel):
    temp: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    condition: Optional[str] = None


class Rankings(BaseModel):
    overall_rank: Optional[int] = None
    overall_total: Optional[int] = None
    group_name: Optional[str] = None
    group_rank: Optional[int] = None
    group_total: Optional[int] = None


class Sources(BaseModel):
    original_url: str = ""
    athlinks_url: str = ""
    # Strava URL can be a single string or a list of strings/dicts
    strava_url: Union[str, list, None] = None
    local_files: list[str] = []


class RaceRecord(BaseModel):
    """Top-level schema for a race metadata.json file."""

    race_metadata: RaceMetadata
    results: Results
    weather: Weather = Weather()
    rankings: Rankings = Rankings()
    sources: Sources = Sources()

    @field_validator("race_metadata")
    @classmethod
    def location_gps_length(cls, v: RaceMetadata) -> RaceMetadata:
        """GPS coords must be a [lat, lon] pair when present."""
        if v.location_gps is not None and len(v.location_gps) != 2:
            raise ValueError("location_gps must be a [lat, lon] pair")
        return v
