"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, History } from "lucide-react";
import { toast } from "sonner";

import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { openCase } from "@/lib/api/cases";
import { listProfiles } from "@/lib/api/profiles";
import { listStations } from "@/lib/api/stations";
import type { DispenseProfile, DispenseStation } from "@/lib/api/types";

export default function OpenCasePage() {
  const router = useRouter();

  const [stations, setStations] = React.useState<DispenseStation[]>([]);
  const [profiles, setProfiles] = React.useState<DispenseProfile[]>([]);
  const [loadingOptions, setLoadingOptions] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);

  const [stationId, setStationId] = React.useState("");
  const [profileId, setProfileId] = React.useState("");
  const [materialLot, setMaterialLot] = React.useState("");
  const [complaint, setComplaint] = React.useState("");
  const [complaintText, setComplaintText] = React.useState("");

  React.useEffect(() => {
    Promise.all([listStations({ limit: 200 }), listProfiles({ limit: 200 })])
      .then(([s, p]) => {
        setStations(s.items);
        setProfiles(p.items);
        if (s.items.length === 1) setStationId(String(s.items[0].station_id));
        if (p.items.length === 1) setProfileId(String(p.items[0].profile_id));
      })
      .catch(() => toast.error("Could not reach the API. Is the backend running?"))
      .finally(() => setLoadingOptions(false));
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!stationId || !profileId) {
      toast.error("Pick a station and a profile.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await openCase({
        station_id: Number(stationId), profile_id: Number(profileId),
        material_lot: materialLot || null, complaint: complaint || null,
        complaint_text: complaintText || null,
      });
      router.push(`/troubleshoot/${created.case_id}`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not open the case.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl flex-1 px-6 py-10">
      <div className="mb-6 flex items-center justify-between">
        <Link
          href="/"
          className={buttonVariants({
            variant: "ghost",
            size: "sm",
            className: "gap-1.5 text-muted-foreground hover:text-foreground",
          })}
        >
          <ArrowLeft className="size-4" />
          Back to Home
        </Link>
        <Link
          href="/cases"
          className={buttonVariants({
            variant: "outline",
            size: "sm",
            className: "gap-1.5 text-xs",
          })}
        >
          <History className="size-3.5" />
          View Past Cases
        </Link>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Open a case</CardTitle>
            <CardDescription>
              Step 1 of the pipeline: links and context. The interview and evidence
              come once the case is open.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-2">
              <Label htmlFor="station">Dispense station</Label>
              <Select value={stationId} onValueChange={(v) => setStationId(v ?? "")} disabled={loadingOptions}>
                <SelectTrigger id="station" className="w-full">
                  {/* Base UI's Select.Value only knows an item's label once that
                     item has rendered inside an opened SelectContent — which
                     never happens for a value set programmatically (the
                     auto-select-when-there's-one-option case below), so it
                     falls back to the raw id. Rendering the label ourselves
                     sidesteps that registry-timing gap entirely. */}
                  <SelectValue placeholder="Select the machine">
                    {(value: string) => stations.find((s) => String(s.station_id) === value)?.name ?? value}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {stations.map((s) => (
                    <SelectItem key={s.station_id} value={String(s.station_id)}>
                      {s.name} &middot; {s.line}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="profile">Dispense profile</Label>
              <Select value={profileId} onValueChange={(v) => setProfileId(v ?? "")} disabled={loadingOptions}>
                <SelectTrigger id="profile" className="w-full">
                  <SelectValue placeholder="Select the job">
                    {(value: string) => profiles.find((p) => String(p.profile_id) === value)?.name ?? value}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {profiles.map((p) => (
                    <SelectItem key={p.profile_id} value={String(p.profile_id)}>
                      {p.name} &middot; {p.material.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="material_lot">Material lot</Label>
              <Input id="material_lot" value={materialLot} onChange={(e) => setMaterialLot(e.target.value)} placeholder="LOT-882" />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="complaint">Complaint</Label>
              <Input id="complaint" value={complaint} onChange={(e) => setComplaint(e.target.value)} placeholder="Inconsistent size shot to shot" />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="complaint_text">Description, in the operator&apos;s words</Label>
              <Textarea id="complaint_text" value={complaintText} onChange={(e) => setComplaintText(e.target.value)} rows={3} />
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button type="submit" disabled={submitting || loadingOptions}>
              {submitting ? "Opening…" : "Open case & continue"}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
