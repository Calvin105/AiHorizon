"""The demo catalog: one station, two materials, and profiles laid out like
the project's sample photos. Run with: uv run python -m app.seed
(or rebuild everything with: uv run python -m app.reset_demo).

The profiles take their geometry from vision/samples/good.json, so a photo
of any 15-dot sample — or a phone photo of one, now that detect() registers
photos to the recipe — measures instead of being refused. The previous
default profile was a 4-dot layout that no sample photo matched.
"""

import json
from pathlib import Path

import app.core.models  # noqa: F401  (register every model first)
from app.core.database import SessionLocal
from app.domains.enums import DispenserClass, MaterialFamily
from app.domains.materials.model import FluidMaterial
from app.domains.profiles.model import DispenseProfile
from app.domains.stations.model import DispenseStation

SAMPLES = Path(__file__).resolve().parents[3] / "vision" / "samples"

#: The profile the live demo runs on — shared with seed_demo_case.py so the
#: scripted case reuses it instead of creating a near-duplicate.
DEMO_PROFILE_NAME = "Standard Dot · 15-point grid"


def sample_geometry() -> dict:
    sidecar = json.loads((SAMPLES / "good.json").read_text())
    return {k: sidecar[k] for k in ("pattern", "width", "height", "profile")}


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(FluidMaterial).count() > 0:
            print("Already seeded, skipping.")
            return

        epoxy = FluidMaterial(
            name="Epoxy A", part_number="EPX-100", family=MaterialFamily.EPOXY,
            two_part=True, thixotropic=True, requires_thaw=False,
            pot_life_hours=8, out_time_hours=4, storage_temp_c=4, filler_particle_um=15,
        )
        silicone = FluidMaterial(
            name="Silicone RTV S-20", part_number="SIL-020", family=MaterialFamily.SILICONE,
            two_part=False, thixotropic=False, requires_thaw=False,
            pot_life_hours=24, out_time_hours=72, storage_temp_c=22,
        )
        db.add_all([epoxy, silicone])
        db.flush()

        station = DispenseStation(
            name="Line 3 Dispenser", line="L3", dispenser_class=DispenserClass.PRESSURE_TIME,
            valve_model="Nordson 741", heated_reservoir=False,
            reports_dispense_order=True, camera_available=True,
        )
        db.add(station)

        geometry = sample_geometry()
        db.add_all([
            DispenseProfile(
                name=DEMO_PROFILE_NAME, material_id=epoxy.material_id,
                needle_gauge="27G", needle_id_um=210,
                set_pressure_kpa=150, set_time_ms=120, standoff_um=300, speed_mm_s=25, set_temp_c=25,
                spec_metric="size_cv", spec_limit="< 0.15", geometry=geometry,
            ),
            DispenseProfile(
                name="Silicone seal dots · 15-point grid", material_id=silicone.material_id,
                needle_gauge="22G", needle_id_um=410,
                set_pressure_kpa=200, set_time_ms=180, standoff_um=450, speed_mm_s=15, set_temp_c=None,
                spec_metric="size_cv", spec_limit="< 0.2", geometry=geometry,
            ),
        ])
        db.commit()
        print(f"Seeded 1 station, 2 materials, 2 profiles (demo profile: {DEMO_PROFILE_NAME!r})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
