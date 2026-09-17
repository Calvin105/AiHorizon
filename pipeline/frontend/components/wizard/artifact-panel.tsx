"use client";

import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ProfileGeometryPattern } from "@/components/profile-geometry-pattern";
import type {
  Case, CauseComparison, CheckResult, CloseCaseResponse, CoarseMatch, FingerprintAxes,
  Ranking, Report, VisionResult,
} from "@/lib/api/types";

export interface Artifacts {
  caseData: Case;
  photoUrl: string | null;
  axes: Partial<FingerprintAxes>;
  vision: VisionResult | null;
  coarse: CoarseMatch[] | null;
  ranking: Ranking | null;
  comparison: CauseComparison[] | null;
  checks: CheckResult[];
  report: Report | null;
  close: CloseCaseResponse | null;
}

const TIER_VARIANT: Record<string, "default" | "secondary" | "destructive"> = {
  T1: "default", T2: "secondary", T3: "secondary", T4: "destructive",
};

function ArtifactCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="pb-2"><CardTitle className="text-sm">{title}</CardTitle></CardHeader>
      <CardContent className="text-sm">{children}</CardContent>
    </Card>
  );
}

export function ArtifactPanel({ artifacts }: { artifacts: Artifacts }) {
  const { caseData } = artifacts;
  const hasAxes = Object.values(artifacts.axes).some((v) => (Array.isArray(v) ? v.length : v));

  return (
    <ScrollArea className="h-full min-h-0">
      <div className="space-y-4 p-4">
        <ArtifactCard title="Case & Profile">
          <p className="font-medium">#{caseData.case_id} &middot; {caseData.complaint ?? "unclassified"}</p>
          <p className="text-muted-foreground">
            {caseData.station.name} ({caseData.station.line}) &middot; {caseData.profile.name} &middot;{" "}
            {caseData.profile.material.name}
          </p>
          {caseData.profile.geometry && (
            <div className="mt-3 border-t pt-2.5">
              <div className="mb-1 text-xs font-medium text-muted-foreground">
                Dispense Pattern Geometry
              </div>
              <ProfileGeometryPattern
                geometry={caseData.profile.geometry}
                specMetric={caseData.profile.spec_metric}
                specLimit={caseData.profile.spec_limit}
                canvasClassName="h-64"
              />
            </div>
          )}
        </ArtifactCard>

        {artifacts.photoUrl && (
          <ArtifactCard title="Photo">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={artifacts.photoUrl} alt="Uploaded dispense photo" className="w-full rounded-md border" />
          </ArtifactCard>
        )}

        {hasAxes && (
          <ArtifactCard title="Answers so far">
            <dl className="space-y-1">
              {artifacts.axes.signature && artifacts.axes.signature.length > 0 && (
                <div><dt className="text-xs text-muted-foreground">signature</dt><dd>{artifacts.axes.signature.join(", ")}</dd></div>
              )}
              {artifacts.axes.trajectory && (
                <div><dt className="text-xs text-muted-foreground">trajectory</dt><dd>{artifacts.axes.trajectory}</dd></div>
              )}
              {artifacts.axes.footprint && (
                <div><dt className="text-xs text-muted-foreground">footprint</dt><dd>{artifacts.axes.footprint}</dd></div>
              )}
              {artifacts.axes.inputs && artifacts.axes.inputs.length > 0 && (
                <div><dt className="text-xs text-muted-foreground">inputs</dt><dd>{artifacts.axes.inputs.join(", ")}</dd></div>
              )}
              {artifacts.axes.response && (
                <div><dt className="text-xs text-muted-foreground">response</dt><dd>{artifacts.axes.response}</dd></div>
              )}
            </dl>
          </ArtifactCard>
        )}

        {artifacts.vision && (
          <ArtifactCard title="Vision (step 3)">
            <Badge variant={artifacts.vision.quality_ok ? "outline" : "destructive"} className="mb-2">
              {artifacts.vision.quality_ok ? "quality ok" : artifacts.vision.quality_reason}
            </Badge>
            {artifacts.vision.quality_ok && (
              <dl className="grid grid-cols-2 gap-x-2 gap-y-1 text-xs">
                {Object.entries(artifacts.vision.signals).map(([k, v]) => (
                  <React.Fragment key={k}>
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd>{typeof v === "number" ? v.toFixed(3) : String(v)}</dd>
                  </React.Fragment>
                ))}
              </dl>
            )}
            <p className="mt-2 text-xs text-muted-foreground">magnitude: {artifacts.vision.magnitude}</p>
          </ArtifactCard>
        )}

        {artifacts.coarse && (
          <ArtifactCard title="Coarse retrieval (step 2b)">
            {artifacts.coarse.length === 0 ? (
              <p className="text-muted-foreground">No similar past cases yet — nothing to pre-load.</p>
            ) : (
              <ul className="space-y-1">
                {artifacts.coarse.map((m) => (
                  <li key={m.case_id} className="flex items-center justify-between">
                    <span>case #{m.case_id} &middot; {m.matched_axes.join(", ")}</span>
                    <Badge variant="outline">{m.score.toFixed(2)}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </ArtifactCard>
        )}

        {artifacts.ranking && (
          <ArtifactCard title="Ranking (step 5)">
            <div className="mb-2 flex flex-wrap gap-2">
              <Badge variant={TIER_VARIANT[artifacts.ranking.tier]}>{artifacts.ranking.tier}</Badge>
              <Badge variant="outline">{artifacts.ranking.agree ? "passes agree" : "passes disagree"}</Badge>
            </div>
            <div className="space-y-2">
              {artifacts.ranking.pass1.slice(0, 4).map((c) => (
                <div key={c.cause_id}>
                  <div className="flex items-center justify-between text-xs">
                    <span>{c.label}</span>
                    <span className="text-muted-foreground">{Math.round(c.likelihood * 100)}%</span>
                  </div>
                  <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
                    <div className="h-full bg-primary" style={{ width: `${c.likelihood * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </ArtifactCard>
        )}

        {artifacts.checks.length > 0 && (
          <ArtifactCard title="Troubleshooting loop (step 6)">
            <ul className="space-y-1">
              {artifacts.checks.map((c) => (
                <li key={c.check_result_id} className="flex items-center justify-between">
                  <span>#{c.sequence} {c.check_name}</span>
                  <Badge variant="outline">{c.outcome ?? "logged"}</Badge>
                </li>
              ))}
            </ul>
          </ArtifactCard>
        )}

        {artifacts.report && (
          <ArtifactCard title="Report (step 7)">
            <div className="mb-2 flex flex-wrap gap-1.5">
              <Badge>{artifacts.report.defect.magnitude}</Badge>
              <Badge variant="outline">{"★".repeat(artifacts.report.defect.stars)}{"☆".repeat(5 - artifacts.report.defect.stars)}</Badge>
            </div>
            {artifacts.report.explanation && <p className="text-xs">{artifacts.report.explanation}</p>}
            <p className="mt-2 text-xs text-muted-foreground">{artifacts.report.disclaimer}</p>
          </ArtifactCard>
        )}

        {artifacts.close && (
          <ArtifactCard title="Closed (step 8)">
            <Badge>{artifacts.close.tier}</Badge>
            {artifacts.close.gaps.length > 0 && (
              <ul className="ml-4 mt-2 list-disc text-xs text-muted-foreground">
                {artifacts.close.gaps.map((g, i) => <li key={i}>{g}</li>)}
              </ul>
            )}
          </ArtifactCard>
        )}
      </div>
    </ScrollArea>
  );
}
