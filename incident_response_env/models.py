"""Typed models exposed by the installable Incident Response environment package."""

from src.models import Action, Observation, State


class IncidentResponseAction(Action):
    """Typed action model for the incident response benchmark."""


class IncidentResponseObservation(Observation):
    """Typed observation model for the incident response benchmark."""


class IncidentResponseState(State):
    """Typed state model for the incident response benchmark."""
