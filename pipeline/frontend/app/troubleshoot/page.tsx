"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Compass,
  Cpu,
  Droplets,
  ExternalLink,
  Eye,
  FlaskConical,
  Gauge,
  History,
  Info,
  Layers,
  Search,
  Sliders,
  Sparkles,
  Thermometer,
  Wrench,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { ProfileGeometryPattern } from "@/components/profile-geometry-pattern";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { openCase } from "@/lib/api/cases";
import { listMaterials } from "@/lib/api/materials";
import { listProfiles } from "@/lib/api/profiles";
import { listStations } from "@/lib/api/stations";
import type { DispenseProfile, DispenseStation, FluidMaterial } from "@/lib/api/types";

const COMPLAINT_PRESETS = [
  "Inconsistent size shot to shot",
  "Bridging / shorting between pads",
  "Missing or starved deposit",
  "Tail / stringing on pull-off",
  "Satellite / splashing droplets",
  "Deposit height drift",
];

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-medium text-foreground">{value ?? "—"}</span>
    </div>
  );
}

function yesNo(val?: boolean | null) {
  return val ? "Yes" : "No";
}

export default function OpenCasePage() {
  const router = useRouter();

  const [stations, setStations] = React.useState<DispenseStation[]>([]);
  const [profiles, setProfiles] = React.useState<DispenseProfile[]>([]);
  const [materials, setMaterials] = React.useState<FluidMaterial[]>([]);
  const [loadingOptions, setLoadingOptions] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);

  const [stationId, setStationId] = React.useState("");
  const [materialId, setMaterialId] = React.useState("");
  const [profileId, setProfileId] = React.useState("");
  const [materialLot, setMaterialLot] = React.useState("");
  const [complaint, setComplaint] = React.useState("");
  const [complaintText, setComplaintText] = React.useState("");

  // Search queries for the item lists
  const [searchMaterial, setSearchMaterial] = React.useState("");
  const [searchStation, setSearchStation] = React.useState("");
  const [searchProfile, setSearchProfile] = React.useState("");

  // Inspector Modal State
  const [inspectItem, setInspectItem] = React.useState<{
    type: "station" | "material" | "profile";
    station?: DispenseStation;
    material?: FluidMaterial;
    profile?: DispenseProfile;
  } | null>(null);

  // Close inspector on Escape key
  React.useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setInspectItem(null);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  React.useEffect(() => {
    Promise.all([
      listStations({ limit: 200 }),
      listProfiles({ limit: 200 }),
      listMaterials({ limit: 200 }),
    ])
      .then(([s, p, m]) => {
        setStations(s.items);
        setProfiles(p.items);
        setMaterials(m.items);
      })
      .catch(() => toast.error("Could not reach the API. Is the backend running?"))
      .finally(() => setLoadingOptions(false));
  }, []);

  // Filter profiles based on selected material if one is chosen
  const filteredProfiles = React.useMemo(() => {
    if (!materialId) return profiles;
    return profiles.filter((p) => String(p.material_id) === materialId);
  }, [profiles, materialId]);

  // Selected object lookups
  const selectedStation = stations.find((s) => String(s.station_id) === stationId);
  const selectedMaterial = materials.find((m) => String(m.material_id) === materialId);
  const selectedProfile = profiles.find((p) => String(p.profile_id) === profileId);

  // When material changes: check if selected profile still matches
  function handleMaterialChange(matId: string | null) {
    const id = matId ?? "";
    setMaterialId(id);
    const matching = profiles.filter((p) => String(p.material_id) === id);
    if (matching.length > 0) {
      if (!matching.some((p) => String(p.profile_id) === profileId)) {
        setProfileId(String(matching[0].profile_id));
      }
    } else {
      setProfileId("");
    }
  }

  // When profile changes: auto-sync material
  function handleProfileChange(profId: string | null) {
    const id = profId ?? "";
    setProfileId(id);
    const p = profiles.find((item) => String(item.profile_id) === id);
    if (p) {
      setMaterialId(String(p.material_id));
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!stationId) {
      toast.error("Please pick a dispense station.");
      return;
    }
    if (!profileId) {
      toast.error("Please pick a dispense profile.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await openCase({
        station_id: Number(stationId),
        profile_id: Number(profileId),
        material_lot: materialLot || null,
        complaint: complaint || null,
        complaint_text: complaintText || null,
      });
      toast.success(`Case #${created.case_id} opened! Starting troubleshooting...`);
      router.push(`/troubleshoot/${created.case_id}`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not open the case.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1520px] space-y-6 px-4 py-8 sm:px-6 lg:px-8 xl:px-12">
      {/* Top Header & Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className={buttonVariants({
              variant: "ghost",
              size: "sm",
              className: "gap-1.5 text-muted-foreground hover:text-foreground",
            })}
          >
            <ArrowLeft className="size-4" />
            <span>Home</span>
          </Link>
          <span className="text-muted-foreground/30">/</span>
          <Link
            href="/cases"
            className="text-xs text-muted-foreground hover:text-foreground hover:underline"
          >
            Past Cases
          </Link>
          <span className="text-muted-foreground/30">/</span>
          <span className="text-xs font-semibold text-foreground">
            Start Troubleshooting
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/profiles"
            className={buttonVariants({
              variant: "ghost",
              size: "sm",
              className: "gap-1.5 text-xs text-muted-foreground hover:text-foreground",
            })}
          >
            <Compass className="size-3.5" />
            <span>Profile Blueprints</span>
          </Link>
          <Link
            href="/cases"
            className={buttonVariants({
              variant: "outline",
              size: "sm",
              className: "gap-1.5 text-xs font-medium",
            })}
          >
            <History className="size-3.5" />
            <span>View Past Cases</span>
          </Link>
        </div>
      </div>

      {/* Hero Title with Wide Subtitle */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-primary/40 bg-primary/10 text-xs font-semibold text-primary">
              Step 1 · Intake
            </Badge>
            <span className="text-xs text-muted-foreground">Setup dispense links & line parameters</span>
          </div>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight md:text-3xl text-foreground">
            Open Case & Start Troubleshooting
          </h1>
          <p className="mt-1 text-sm text-muted-foreground max-w-3xl">
            Select the hardware station, fluid material, and dispense profile. You can check the complete technical specifications and pattern geometry of any listed item at any time before proceeding.
          </p>
        </div>
      </div>

      {/* Main Wide 2-Column Dashboard Grid */}
      <div className="grid gap-8 lg:grid-cols-12">
        {/* Left Column: Intake Form (7 cols) */}
        <div className="lg:col-span-7">
          <form onSubmit={handleSubmit} className="space-y-6">
            <Card className="shadow-xs">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg">Machine & Process Selection</CardTitle>
                <CardDescription>
                  Choose the hardware station and fluid job running on the line.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Dispense Station */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="station" className="flex items-center gap-1.5 text-xs font-semibold">
                      <Wrench className="size-3.5 text-primary" />
                      Dispense Station
                    </Label>
                    {selectedStation && (
                      <button
                        type="button"
                        onClick={() => setInspectItem({ type: "station", station: selectedStation })}
                        className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
                      >
                        <Eye className="size-3" /> Check station details
                      </button>
                    )}
                  </div>
                  <Select
                    value={stationId}
                    onValueChange={(v) => setStationId(v ?? "")}
                    disabled={loadingOptions}
                  >
                    <SelectTrigger id="station" className="w-full">
                      <SelectValue placeholder="Select station...">
                        {(value: string) => {
                          const s = stations.find((item) => String(item.station_id) === value);
                          return s ? `${s.name} (${s.line}) · ${s.dispenser_class}` : value;
                        }}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {stations.map((s) => (
                        <SelectItem key={s.station_id} value={String(s.station_id)}>
                          <div className="flex items-center justify-between w-full gap-3">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{s.name}</span>
                              <span className="text-xs text-muted-foreground">({s.line})</span>
                              <span className="text-xs text-muted-foreground">· {s.dispenser_class}</span>
                            </div>
                            {s.valve_model && (
                              <span className="text-[10px] text-muted-foreground font-mono">
                                {s.valve_model}
                              </span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>
                      {selectedStation
                        ? `${selectedStation.line} · ${selectedStation.dispenser_class} ${selectedStation.valve_model ? `(${selectedStation.valve_model})` : ""}`
                        : "Select hardware station to verify valve & dispenser class."}
                    </span>
                    {selectedStation && (
                      <button
                        type="button"
                        onClick={() => setInspectItem({ type: "station", station: selectedStation })}
                        className="font-medium text-foreground hover:underline"
                      >
                        Full specs &rarr;
                      </button>
                    )}
                  </div>
                </div>

                {/* Fluid Material Dropdown */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="material" className="flex items-center gap-1.5 text-xs font-semibold">
                      <FlaskConical className="size-3.5 text-primary" />
                      Fluid Material
                    </Label>
                    {selectedMaterial ? (
                      <button
                        type="button"
                        onClick={() => setInspectItem({ type: "material", material: selectedMaterial })}
                        className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
                      >
                        <Eye className="size-3" /> Check material details
                      </button>
                    ) : (
                      <span className="text-[11px] text-muted-foreground">
                        Filters suitable profiles
                      </span>
                    )}
                  </div>
                  <Select
                    value={materialId}
                    onValueChange={handleMaterialChange}
                    disabled={loadingOptions}
                  >
                    <SelectTrigger id="material" className="w-full">
                      <SelectValue placeholder="Select fluid material...">
                        {(value: string) => {
                          const m = materials.find((item) => String(item.material_id) === value);
                          return m ? `${m.name} ${m.part_number ? `(${m.part_number})` : ""} · ${m.family}` : value;
                        }}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {materials.map((m) => (
                        <SelectItem key={m.material_id} value={String(m.material_id)}>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{m.name}</span>
                            {m.part_number && (
                              <span className="text-xs text-muted-foreground font-mono">({m.part_number})</span>
                            )}
                            <Badge variant="outline" className="text-[10px] uppercase">
                              {m.family}
                            </Badge>
                            {m.two_part && <span className="text-[11px] text-muted-foreground">· 2-part</span>}
                            {m.pot_life_hours && (
                              <span className="text-[10px] text-muted-foreground">· pot life {m.pot_life_hours}h</span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>
                      {selectedMaterial
                        ? `${selectedMaterial.family} · ${selectedMaterial.two_part ? "2-part formulation" : "1-component"} ${selectedMaterial.pot_life_hours ? `· ${selectedMaterial.pot_life_hours}h pot life` : ""}`
                        : "Pick a material to filter compatible profiles & verify rheology limits."}
                    </span>
                    {selectedMaterial && (
                      <button
                        type="button"
                        onClick={() => setInspectItem({ type: "material", material: selectedMaterial })}
                        className="font-medium text-foreground hover:underline"
                      >
                        Full specs &rarr;
                      </button>
                    )}
                  </div>
                </div>

                {/* Dispense Profile Dropdown */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="profile" className="flex items-center gap-1.5 text-xs font-semibold">
                      <Compass className="size-3.5 text-primary" />
                      Dispense Profile & Pattern
                    </Label>
                    {selectedProfile ? (
                      <button
                        type="button"
                        onClick={() => setInspectItem({ type: "profile", profile: selectedProfile })}
                        className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
                      >
                        <Eye className="size-3" /> Check profile & pattern geometry
                      </button>
                    ) : filteredProfiles.length > 0 ? (
                      <span className="text-[11px] text-muted-foreground">
                        {filteredProfiles.length} suitable profile{filteredProfiles.length === 1 ? "" : "s"}
                      </span>
                    ) : null}
                  </div>
                  <Select
                    value={profileId}
                    onValueChange={handleProfileChange}
                    disabled={loadingOptions}
                  >
                    <SelectTrigger id="profile" className="w-full">
                      <SelectValue placeholder="Select dispense profile...">
                        {(value: string) => {
                          const p = profiles.find((item) => String(item.profile_id) === value);
                          return p ? `${p.name} · ${p.needle_gauge ?? ""} · ${p.spec_metric ?? "nominal"}` : value;
                        }}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {filteredProfiles.map((p) => (
                        <SelectItem key={p.profile_id} value={String(p.profile_id)}>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{p.name}</span>
                            {p.needle_gauge && (
                              <Badge variant="secondary" className="text-[10px]">
                                {p.needle_gauge}
                              </Badge>
                            )}
                            <span className="text-xs text-muted-foreground">· {p.material.name}</span>
                            {p.spec_metric && p.spec_limit && (
                              <span className="text-[10px] text-muted-foreground">
                                ({p.spec_metric} {p.spec_limit})
                              </span>
                            )}
                            {p.geometry?.pattern && (
                              <Badge variant="outline" className="text-[9px] uppercase">
                                {p.geometry.pattern}
                              </Badge>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>
                      {selectedProfile
                        ? `${selectedProfile.needle_gauge ?? "Standard needle"} · ${selectedProfile.set_pressure_kpa ? `${selectedProfile.set_pressure_kpa} kPa` : "nominal pressure"} · ${selectedProfile.geometry?.pattern ? `Pattern: ${selectedProfile.geometry.pattern}` : "Standard geometry"}`
                        : "Pick a profile to load calibrated needle, pressure, and tolerance limits."}
                    </span>
                    {selectedProfile && (
                      <button
                        type="button"
                        onClick={() => setInspectItem({ type: "profile", profile: selectedProfile })}
                        className="font-medium text-foreground hover:underline"
                      >
                        Inspect geometry &rarr;
                      </button>
                    )}
                  </div>
                </div>

                {/* Material Lot */}
                <div className="space-y-1.5">
                  <Label htmlFor="material_lot" className="text-xs font-semibold">
                    Material Lot / Batch ID (Optional)
                  </Label>
                  <Input
                    id="material_lot"
                    value={materialLot}
                    onChange={(e) => setMaterialLot(e.target.value)}
                    placeholder="e.g. LOT-2026-A or 2409-X"
                    className="text-sm"
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Helps cross-reference batch-specific shelf-life and thaw histories in Step 8.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Defect Complaint Card */}
            <Card className="shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Observed Defect Complaint</CardTitle>
                <CardDescription>
                  Summarize what went wrong on the board or substrate.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Preset Chips */}
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Quick Presets:</Label>
                  <div className="flex flex-wrap gap-1.5">
                    {COMPLAINT_PRESETS.map((preset) => {
                      const active = complaint === preset;
                      return (
                        <button
                          key={preset}
                          type="button"
                          onClick={() => setComplaint(preset)}
                          className={`rounded-md border px-2.5 py-1 text-xs transition-colors ${
                            active
                              ? "border-primary bg-primary text-primary-foreground font-medium"
                              : "bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        >
                          {preset}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Complaint Title Input */}
                <div className="space-y-1.5">
                  <Label htmlFor="complaint" className="text-xs font-semibold">
                    Defect Title / Summary
                  </Label>
                  <Input
                    id="complaint"
                    value={complaint}
                    onChange={(e) => setComplaint(e.target.value)}
                    placeholder="e.g. Inconsistent size shot to shot"
                    className="text-sm font-medium"
                  />
                </div>

                {/* Complaint Description / Operator Notes */}
                <div className="space-y-1.5">
                  <Label htmlFor="complaint_text" className="text-xs font-semibold">
                    Operator Notes / Freeform Description
                  </Label>
                  <Textarea
                    id="complaint_text"
                    value={complaintText}
                    onChange={(e) => setComplaintText(e.target.value)}
                    rows={3}
                    placeholder="Describe specific symptoms (e.g. started after syringe change, tailing on rightmost pads, pressure dropped)..."
                    className="text-sm"
                  />
                </div>
              </CardContent>
              <CardFooter className="border-t bg-muted/20 pt-4">
                <Button
                  type="submit"
                  size="lg"
                  disabled={submitting || loadingOptions}
                  className="w-full gap-2 font-semibold shadow-md"
                >
                  <Sparkles className="size-4" />
                  {submitting ? "Opening Case & Launching..." : "Start Troubleshooting Wizard →"}
                </Button>
              </CardFooter>
            </Card>
          </form>
        </div>

        {/* Right Column: Live Confirmation & Option Reference (5 cols) */}
        <div className="space-y-6 lg:col-span-5">
          {/* Live Confirmation Card */}
          <Card className="border-primary/20 bg-muted/10 shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Info className="size-4 text-primary" />
                  Live Detail Confirmation
                </CardTitle>
                <Badge variant="outline" className="text-[10px]">
                  Active Selection
                </Badge>
              </div>
              <CardDescription>
                Confirm station, material, and profile parameters match your line setup.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              {/* Station Block */}
              <div className="rounded-md border bg-background p-3 space-y-2">
                <div className="flex items-center justify-between font-semibold">
                  <span className="flex items-center gap-1.5 text-foreground">
                    <Wrench className="size-3.5 text-primary" /> Station
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="secondary" className="text-[10px]">
                      {selectedStation ? selectedStation.name : "—"}
                    </Badge>
                    {selectedStation && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-6 gap-1 px-1.5 text-[10px] text-primary hover:bg-primary/10"
                        onClick={() => setInspectItem({ type: "station", station: selectedStation })}
                      >
                        <Eye className="size-3" /> Check Details
                      </Button>
                    )}
                  </div>
                </div>
                <div className="space-y-1 text-muted-foreground">
                  <Field label="Line" value={selectedStation?.line ?? "—"} />
                  <Field label="Dispenser class" value={selectedStation?.dispenser_class ?? "—"} />
                  <Field label="Valve model" value={selectedStation?.valve_model ?? "—"} />
                  <Field label="Heated reservoir" value={selectedStation ? yesNo(selectedStation.heated_reservoir) : "—"} />
                  <Field label="Camera available" value={selectedStation ? yesNo(selectedStation.camera_available) : "—"} />
                </div>
              </div>

              {/* Material Block */}
              <div className="rounded-md border bg-background p-3 space-y-2">
                <div className="flex items-center justify-between font-semibold">
                  <span className="flex items-center gap-1.5 text-foreground">
                    <FlaskConical className="size-3.5 text-primary" /> Fluid Material
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="secondary" className="text-[10px]">
                      {selectedMaterial ? selectedMaterial.name : "—"}
                    </Badge>
                    {selectedMaterial && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-6 gap-1 px-1.5 text-[10px] text-primary hover:bg-primary/10"
                        onClick={() => setInspectItem({ type: "material", material: selectedMaterial })}
                      >
                        <Eye className="size-3" /> Check Details
                      </Button>
                    )}
                  </div>
                </div>
                <div className="space-y-1 text-muted-foreground">
                  <Field label="Part #" value={selectedMaterial?.part_number ?? "—"} />
                  <Field label="Family" value={selectedMaterial?.family ?? "—"} />
                  <Field
                    label="Chemistry"
                    value={
                      selectedMaterial
                        ? selectedMaterial.two_part
                          ? "Two-part formulation"
                          : "Single component"
                        : "—"
                    }
                  />
                  <Field
                    label="Thixotropic"
                    value={selectedMaterial ? yesNo(selectedMaterial.thixotropic) : "—"}
                  />
                  <Field
                    label="Pot life limit"
                    value={selectedMaterial?.pot_life_hours ? `${selectedMaterial.pot_life_hours}h` : "—"}
                  />
                  <Field
                    label="Out-time limit"
                    value={selectedMaterial?.out_time_hours ? `${selectedMaterial.out_time_hours}h` : "—"}
                  />
                  <Field
                    label="Storage temp"
                    value={selectedMaterial?.storage_temp_c != null ? `${selectedMaterial.storage_temp_c} °C` : "—"}
                  />
                  <Field
                    label="Filler particle"
                    value={
                      selectedMaterial?.filler_particle_um
                        ? `${selectedMaterial.filler_particle_um} µm`
                        : selectedMaterial
                          ? "None"
                          : "—"
                    }
                  />
                </div>
              </div>

              {/* Profile Block */}
              <div className="rounded-md border bg-background p-3 space-y-2">
                <div className="flex items-center justify-between font-semibold">
                  <span className="flex items-center gap-1.5 text-foreground">
                    <Compass className="size-3.5 text-primary" /> Dispense Profile
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="secondary" className="text-[10px]">
                      {selectedProfile ? selectedProfile.name : "—"}
                    </Badge>
                    {selectedProfile && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-6 gap-1 px-1.5 text-[10px] text-primary hover:bg-primary/10"
                        onClick={() => setInspectItem({ type: "profile", profile: selectedProfile })}
                      >
                        <Eye className="size-3" /> Check Specs
                      </Button>
                    )}
                  </div>
                </div>
                <div className="space-y-1 text-muted-foreground">
                  <Field label="Needle gauge" value={selectedProfile?.needle_gauge ?? "—"} />
                  <Field label="Needle ID" value={selectedProfile?.needle_id_um ? `${selectedProfile.needle_id_um} µm` : "—"} />
                  <Field label="Set pressure" value={selectedProfile?.set_pressure_kpa ? `${selectedProfile.set_pressure_kpa} kPa` : "—"} />
                  <Field label="Set time" value={selectedProfile?.set_time_ms ? `${selectedProfile.set_time_ms} ms` : "—"} />
                  <Field label="Standoff" value={selectedProfile?.standoff_um ? `${selectedProfile.standoff_um} µm` : "—"} />
                  <Field label="Speed" value={selectedProfile?.speed_mm_s ? `${selectedProfile.speed_mm_s} mm/s` : "—"} />
                  <Field label="Set temperature" value={selectedProfile?.set_temp_c ? `${selectedProfile.set_temp_c} °C` : "—"} />
                  <Field label="Spec limit" value={selectedProfile?.spec_metric ? `${selectedProfile.spec_metric} ${selectedProfile.spec_limit}` : "—"} />

                  <div className="pt-2 border-t mt-2 flex items-center justify-between">
                    <span className="text-muted-foreground">Pattern</span>
                    {selectedProfile?.geometry ? (
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-foreground">
                          {selectedProfile.geometry.pattern.toUpperCase()}
                        </span>
                        <button
                          type="button"
                          onClick={() => setInspectItem({ type: "profile", profile: selectedProfile })}
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
                        >
                          <Eye className="size-3" /> Inspect Pattern
                        </button>
                        <Link
                          href={`/profiles/${selectedProfile.profile_id}`}
                          target="_blank"
                          className="inline-flex items-center gap-1 text-[11px] text-sky-500 hover:underline"
                        >
                          Blueprint <ExternalLink className="size-3" />
                        </Link>
                      </div>
                    ) : (
                      <span className="font-mono font-medium text-foreground">—</span>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Option Reference: Browse & Pick From All with Search and Details Inspection */}
          <Card className="shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">Browse Available Options & Specs</CardTitle>
                  <CardDescription className="text-xs">
                    Inspect technical details of any candidate item to confirm suitability.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="materials" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="materials" className="text-xs">
                    Materials ({materials.length})
                  </TabsTrigger>
                  <TabsTrigger value="stations" className="text-xs">
                    Stations ({stations.length})
                  </TabsTrigger>
                  <TabsTrigger value="profiles" className="text-xs">
                    Profiles ({profiles.length})
                  </TabsTrigger>
                </TabsList>

                {/* Materials Tab */}
                <TabsContent value="materials" className="mt-3 space-y-2">
                  <div className="relative mb-2">
                    <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
                    <Input
                      placeholder="Search material name, part #, or chemistry..."
                      value={searchMaterial}
                      onChange={(e) => setSearchMaterial(e.target.value)}
                      className="h-8 pl-8 text-xs"
                    />
                  </div>
                  <div className="max-h-72 overflow-y-auto pr-1 space-y-2">
                    {materials
                      .filter((m) => {
                        if (!searchMaterial.trim()) return true;
                        const q = searchMaterial.toLowerCase();
                        return (
                          m.name.toLowerCase().includes(q) ||
                          (m.part_number && m.part_number.toLowerCase().includes(q)) ||
                          m.family.toLowerCase().includes(q)
                        );
                      })
                      .map((m) => {
                        const isSelected = String(m.material_id) === materialId;
                        return (
                          <div
                            key={m.material_id}
                            className={`flex items-center justify-between rounded-md border p-2.5 text-xs transition-colors ${
                              isSelected ? "border-primary bg-primary/5 shadow-xs" : "bg-card hover:bg-muted/40"
                            }`}
                          >
                            <div className="space-y-0.5 max-w-[62%]">
                              <div className="font-semibold text-foreground flex items-center gap-1.5 flex-wrap">
                                {m.name}
                                {m.part_number && (
                                  <span className="font-mono text-[10px] text-muted-foreground">
                                    #{m.part_number}
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-muted-foreground">
                                {m.family} &middot; {m.two_part ? "2-part" : "1-component"}
                                {m.pot_life_hours ? ` · pot life ${m.pot_life_hours}h` : ""}
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-foreground"
                                onClick={() => setInspectItem({ type: "material", material: m })}
                              >
                                <Eye className="size-3" />
                                <span>Details</span>
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant={isSelected ? "secondary" : "outline"}
                                className="h-7 text-xs font-medium"
                                onClick={() => handleMaterialChange(String(m.material_id))}
                              >
                                {isSelected ? <Check className="size-3 text-emerald-600 mr-1" /> : null}
                                {isSelected ? "Selected" : "Use this"}
                              </Button>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </TabsContent>

                {/* Stations Tab */}
                <TabsContent value="stations" className="mt-3 space-y-2">
                  <div className="relative mb-2">
                    <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
                    <Input
                      placeholder="Search station name, line, or valve..."
                      value={searchStation}
                      onChange={(e) => setSearchStation(e.target.value)}
                      className="h-8 pl-8 text-xs"
                    />
                  </div>
                  <div className="max-h-72 overflow-y-auto pr-1 space-y-2">
                    {stations
                      .filter((s) => {
                        if (!searchStation.trim()) return true;
                        const q = searchStation.toLowerCase();
                        return (
                          s.name.toLowerCase().includes(q) ||
                          s.line.toLowerCase().includes(q) ||
                          s.dispenser_class.toLowerCase().includes(q) ||
                          (s.valve_model && s.valve_model.toLowerCase().includes(q))
                        );
                      })
                      .map((s) => {
                        const isSelected = String(s.station_id) === stationId;
                        return (
                          <div
                            key={s.station_id}
                            className={`flex items-center justify-between rounded-md border p-2.5 text-xs transition-colors ${
                              isSelected ? "border-primary bg-primary/5 shadow-xs" : "bg-card hover:bg-muted/40"
                            }`}
                          >
                            <div className="space-y-0.5 max-w-[62%]">
                              <div className="font-semibold text-foreground flex items-center gap-1.5 flex-wrap">
                                {s.name}
                                <Badge variant="outline" className="text-[10px]">{s.line}</Badge>
                              </div>
                              <div className="text-[11px] text-muted-foreground">
                                {s.dispenser_class} {s.valve_model ? `· ${s.valve_model}` : ""}
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-foreground"
                                onClick={() => setInspectItem({ type: "station", station: s })}
                              >
                                <Eye className="size-3" />
                                <span>Details</span>
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant={isSelected ? "secondary" : "outline"}
                                className="h-7 text-xs font-medium"
                                onClick={() => setStationId(String(s.station_id))}
                              >
                                {isSelected ? <Check className="size-3 text-emerald-600 mr-1" /> : null}
                                {isSelected ? "Selected" : "Use this"}
                              </Button>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </TabsContent>

                {/* Profiles Tab */}
                <TabsContent value="profiles" className="mt-3 space-y-2">
                  <div className="relative mb-2">
                    <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
                    <Input
                      placeholder="Search profile name, needle, or material..."
                      value={searchProfile}
                      onChange={(e) => setSearchProfile(e.target.value)}
                      className="h-8 pl-8 text-xs"
                    />
                  </div>
                  <div className="max-h-72 overflow-y-auto pr-1 space-y-2">
                    {profiles
                      .filter((p) => {
                        if (!searchProfile.trim()) return true;
                        const q = searchProfile.toLowerCase();
                        return (
                          p.name.toLowerCase().includes(q) ||
                          (p.needle_gauge && p.needle_gauge.toLowerCase().includes(q)) ||
                          p.material.name.toLowerCase().includes(q) ||
                          (p.geometry?.pattern && p.geometry.pattern.toLowerCase().includes(q))
                        );
                      })
                      .map((p) => {
                        const isSelected = String(p.profile_id) === profileId;
                        return (
                          <div
                            key={p.profile_id}
                            className={`flex items-center justify-between rounded-md border p-2.5 text-xs transition-colors ${
                              isSelected ? "border-primary bg-primary/5 shadow-xs" : "bg-card hover:bg-muted/40"
                            }`}
                          >
                            <div className="space-y-0.5 max-w-[62%]">
                              <div className="font-semibold text-foreground flex items-center gap-1.5 flex-wrap">
                                {p.name}
                                {p.needle_gauge && (
                                  <Badge variant="secondary" className="text-[10px]">{p.needle_gauge}</Badge>
                                )}
                                {p.geometry?.pattern && (
                                  <Badge variant="outline" className="text-[9px] uppercase">{p.geometry.pattern}</Badge>
                                )}
                              </div>
                              <div className="text-[11px] text-muted-foreground">
                                {p.material.name} &middot; {p.set_pressure_kpa ? `${p.set_pressure_kpa} kPa` : "nominal pressure"}
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-foreground"
                                onClick={() => setInspectItem({ type: "profile", profile: p })}
                              >
                                <Eye className="size-3" />
                                <span>Details</span>
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant={isSelected ? "secondary" : "outline"}
                                className="h-7 text-xs font-medium"
                                onClick={() => handleProfileChange(String(p.profile_id))}
                              >
                                {isSelected ? <Check className="size-3 text-emerald-600 mr-1" /> : null}
                                {isSelected ? "Selected" : "Use this"}
                              </Button>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Comprehensive Details Inspector Modal */}
      {inspectItem && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 sm:p-6"
          onClick={() => setInspectItem(null)}
        >
          <div
            className="w-full max-w-3xl max-h-[90vh] flex flex-col rounded-xl border bg-card text-card-foreground shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b px-6 py-4 bg-muted/20">
              <div className="flex items-center gap-2.5">
                {inspectItem.type === "station" && <Wrench className="size-5 text-primary" />}
                {inspectItem.type === "material" && <FlaskConical className="size-5 text-primary" />}
                {inspectItem.type === "profile" && <Compass className="size-5 text-primary" />}
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px] uppercase font-semibold">
                      {inspectItem.type === "station" && "Dispense Station Details"}
                      {inspectItem.type === "material" && "Fluid Material Chemistry"}
                      {inspectItem.type === "profile" && "Dispense Profile & Pattern Geometry"}
                    </Badge>
                  </div>
                  <h2 className="text-lg font-bold text-foreground mt-0.5">
                    {inspectItem.station?.name}
                    {inspectItem.material?.name}
                    {inspectItem.profile?.name}
                  </h2>
                </div>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-8 rounded-full"
                onClick={() => setInspectItem(null)}
              >
                <X className="size-4" />
                <span className="sr-only">Close</span>
              </Button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Station Inspector */}
              {inspectItem.type === "station" && inspectItem.station && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Production Line</span>
                      <p className="text-sm font-semibold">{inspectItem.station.line}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Dispenser Class</span>
                      <p className="text-sm font-semibold font-mono">{inspectItem.station.dispenser_class}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Valve Model</span>
                      <p className="text-sm font-semibold font-mono">{inspectItem.station.valve_model ?? "Standard"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Heated Reservoir</span>
                      <p className="text-sm font-semibold">{yesNo(inspectItem.station.heated_reservoir)}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Camera Available</span>
                      <p className="text-sm font-semibold">{yesNo(inspectItem.station.camera_available)}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Station ID</span>
                      <p className="text-sm font-semibold font-mono">#{inspectItem.station.station_id}</p>
                    </div>
                  </div>

                  {/* Candidate Profiles for this station */}
                  <div className="rounded-lg border p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold uppercase text-muted-foreground">
                        Candidate Dispense Profiles for this Machine Class ({inspectItem.station.dispenser_class})
                      </h3>
                      <span className="text-[11px] text-muted-foreground">
                        {profiles.length} profiles available
                      </span>
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {profiles.map((p) => (
                        <div key={p.profile_id} className="flex items-center justify-between rounded-md border bg-muted/5 p-2.5 text-xs">
                          <div>
                            <span className="font-semibold">{p.name}</span>
                            {p.needle_gauge && <Badge variant="secondary" className="text-[10px] ml-1.5">{p.needle_gauge}</Badge>}
                            <span className="text-muted-foreground ml-2">· {p.material.name}</span>
                          </div>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            className="h-6 text-[11px]"
                            onClick={() => {
                              setStationId(String(inspectItem.station?.station_id));
                              handleProfileChange(String(p.profile_id));
                              setInspectItem(null);
                              toast.success(`Selected ${inspectItem.station?.name} & ${p.name}`);
                            }}
                          >
                            Pair this profile
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Material Inspector */}
              {inspectItem.type === "material" && inspectItem.material && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Part Number</span>
                      <p className="text-sm font-semibold font-mono">{inspectItem.material.part_number ?? "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Chemical Family</span>
                      <p className="text-sm font-semibold capitalize">{inspectItem.material.family}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Formulation</span>
                      <p className="text-sm font-semibold">{inspectItem.material.two_part ? "2-part mixture" : "1-part component"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Thixotropic</span>
                      <p className="text-sm font-semibold">{yesNo(inspectItem.material.thixotropic)}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Pot Life Limit</span>
                      <p className="text-sm font-semibold">{inspectItem.material.pot_life_hours ? `${inspectItem.material.pot_life_hours} hours` : "N/A"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Out-Time Limit</span>
                      <p className="text-sm font-semibold">{inspectItem.material.out_time_hours ? `${inspectItem.material.out_time_hours} hours` : "N/A"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Storage Temp</span>
                      <p className="text-sm font-semibold">{inspectItem.material.storage_temp_c != null ? `${inspectItem.material.storage_temp_c} °C` : "Ambient"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Filler Particle</span>
                      <p className="text-sm font-semibold">{inspectItem.material.filler_particle_um ? `${inspectItem.material.filler_particle_um} µm` : "None (Unfilled)"}</p>
                    </div>
                  </div>

                  {/* Matching Profiles that use this material */}
                  <div className="rounded-lg border p-4 space-y-3">
                    <h3 className="text-xs font-bold uppercase text-muted-foreground">
                      Compatible Dispense Profiles Using {inspectItem.material.name}
                    </h3>
                    <div className="space-y-2">
                      {profiles
                        .filter((p) => p.material_id === inspectItem.material?.material_id)
                        .map((p) => (
                          <div key={p.profile_id} className="flex items-center justify-between rounded-md border bg-muted/5 p-2.5 text-xs">
                            <div>
                              <span className="font-semibold">{p.name}</span>
                              {p.needle_gauge && <Badge variant="secondary" className="text-[10px] ml-2">{p.needle_gauge}</Badge>}
                              {p.geometry?.pattern && <span className="text-muted-foreground ml-2">· Pattern: {p.geometry.pattern}</span>}
                            </div>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              className="h-6 text-[11px]"
                              onClick={() => {
                                handleMaterialChange(String(inspectItem.material?.material_id));
                                handleProfileChange(String(p.profile_id));
                                setInspectItem(null);
                                toast.success(`Selected material and profile ${p.name}`);
                              }}
                            >
                              Use this profile
                            </Button>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Profile Inspector with Pattern Geometry */}
              {inspectItem.type === "profile" && inspectItem.profile && (
                <div className="space-y-6">
                  {/* Parameter Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Needle Gauge</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.needle_gauge ?? "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Needle Inner Diam.</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.needle_id_um ? `${inspectItem.profile.needle_id_um} µm` : "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Dispense Pressure</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.set_pressure_kpa ? `${inspectItem.profile.set_pressure_kpa} kPa` : "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Dispense Shot Time</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.set_time_ms ? `${inspectItem.profile.set_time_ms} ms` : "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Standoff Height</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.standoff_um ? `${inspectItem.profile.standoff_um} µm` : "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Robot Speed</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.speed_mm_s ? `${inspectItem.profile.speed_mm_s} mm/s` : "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Set Temperature</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.set_temp_c ? `${inspectItem.profile.set_temp_c} °C` : "—"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 space-y-1">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Inspection Spec</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.spec_metric ? `${inspectItem.profile.spec_metric} ${inspectItem.profile.spec_limit}` : "Nominal"}</p>
                    </div>
                  </div>

                  {/* Associated Fluid Material */}
                  <div className="rounded-lg border p-3 bg-muted/10 flex items-center justify-between">
                    <div>
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Configured Fluid Material</span>
                      <p className="text-sm font-semibold">{inspectItem.profile.material.name} ({inspectItem.profile.material.family})</p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="text-xs text-primary gap-1"
                      onClick={() => setInspectItem({ type: "material", material: inspectItem.profile?.material })}
                    >
                      <Eye className="size-3" /> Inspect Material Specs
                    </Button>
                  </div>

                  {/* Pattern Geometry Preview */}
                  {inspectItem.profile.geometry ? (
                    <div className="rounded-lg border p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-xs font-bold uppercase text-foreground">
                            Dispense Pattern Geometry ({inspectItem.profile.geometry.pattern.toUpperCase()})
                          </h3>
                          <p className="text-[11px] text-muted-foreground">
                            Hover over coordinates and points to inspect calibrated Cartesian positions (mm).
                          </p>
                        </div>
                        <Link
                          href={`/profiles/${inspectItem.profile.profile_id}`}
                          target="_blank"
                          className="inline-flex items-center gap-1 text-xs text-sky-500 hover:underline"
                        >
                          Open Blueprint Page <ExternalLink className="size-3" />
                        </Link>
                      </div>
                      <div className="rounded-lg border bg-black/95 overflow-hidden">
                        <ProfileGeometryPattern
                          geometry={inspectItem.profile.geometry}
                          specMetric={inspectItem.profile.spec_metric}
                          specLimit={inspectItem.profile.spec_limit}
                          className="border-0"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border p-4 text-center text-xs text-muted-foreground">
                      No Cartesian coordinate array defined for this profile.
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between border-t px-6 py-4 bg-muted/20">
              <Button
                type="button"
                variant="outline"
                onClick={() => setInspectItem(null)}
              >
                Close
              </Button>
              <Button
                type="button"
                className="gap-1.5 font-semibold shadow-xs"
                onClick={() => {
                  if (inspectItem.type === "station" && inspectItem.station) {
                    setStationId(String(inspectItem.station.station_id));
                    toast.success(`Selected station: ${inspectItem.station.name}`);
                  } else if (inspectItem.type === "material" && inspectItem.material) {
                    handleMaterialChange(String(inspectItem.material.material_id));
                    toast.success(`Selected material: ${inspectItem.material.name}`);
                  } else if (inspectItem.type === "profile" && inspectItem.profile) {
                    handleProfileChange(String(inspectItem.profile.profile_id));
                    toast.success(`Selected profile: ${inspectItem.profile.name}`);
                  }
                  setInspectItem(null);
                }}
              >
                <Check className="size-4" />
                Select this {inspectItem.type} for Intake
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
