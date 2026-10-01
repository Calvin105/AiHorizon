from pydantic import BaseModel, model_validator

from app.core.schema import ORMModel
from app.domains.materials.schema import FluidMaterialRead
from app.domains.vision.magnitude import is_size_cv_spec


def _check_size_cv_spec(spec_metric: str | None, spec_limit: str | None) -> None:
    """A profile that says its spec is a size_cv has to state one. "500±50"
    under size_cv used to be stored as-is and read back as a limit of 500,
    so every photo on the profile measured in spec."""
    if spec_metric == "size_cv" and spec_limit and not is_size_cv_spec(spec_limit):
        raise ValueError(
            "a size_cv spec_limit is a coefficient of variation between 0 and 1, written like "
            f"'< 0.15' — got {spec_limit!r}. Use another spec_metric for a size or diameter tolerance."
        )


class GeometryPoint(BaseModel):
    """Field names match vision/detect/profile.py's ProfilePoint exactly
    (index, cx, cy, r) — this is deliberately the same dict vision/synth
    writes into every sample's sidecar, not a re-shaped version of it."""

    index: int
    cx: float
    cy: float
    r: float


class Geometry(BaseModel):
    """Mirrors vision/detect's profile_data shape exactly — same dict can be
    passed straight to detect(raw, profile_data). ``r`` per point is the
    target radius, ``count`` is len(profile), pitch comes from cx/cy."""

    pattern: str
    width: float | None = None
    height: float | None = None
    profile: list[GeometryPoint] = []


class DispenseProfileBase(BaseModel):
    name: str
    material_id: int
    needle_gauge: str | None = None
    needle_id_um: float | None = None
    set_pressure_kpa: float | None = None
    set_time_ms: float | None = None
    standoff_um: float | None = None
    speed_mm_s: float | None = None
    set_temp_c: float | None = None
    spec_metric: str | None = None
    spec_limit: str | None = None
    geometry: Geometry | None = None


class DispenseProfileCreate(DispenseProfileBase):
    @model_validator(mode="after")
    def _spec_is_consistent(self):
        _check_size_cv_spec(self.spec_metric, self.spec_limit)
        return self


class DispenseProfileUpdate(BaseModel):
    name: str | None = None
    material_id: int | None = None
    needle_gauge: str | None = None
    needle_id_um: float | None = None
    set_pressure_kpa: float | None = None
    set_time_ms: float | None = None
    standoff_um: float | None = None
    speed_mm_s: float | None = None
    set_temp_c: float | None = None
    spec_metric: str | None = None
    spec_limit: str | None = None
    geometry: Geometry | None = None

    @model_validator(mode="after")
    def _spec_is_consistent(self):
        _check_size_cv_spec(self.spec_metric, self.spec_limit)
        return self


class DispenseProfileRead(DispenseProfileBase, ORMModel):
    profile_id: int


class DispenseProfileReadWithMaterial(DispenseProfileRead):
    material: FluidMaterialRead
