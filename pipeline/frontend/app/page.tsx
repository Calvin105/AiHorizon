import Link from "next/link";
import { FilePlus2 } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">NSW Automation</h1>
      <p className="max-w-md text-muted-foreground">
        Dispense-defect troubleshooting pipeline — intake, vision, ranking, the
        troubleshooting loop, and the report, end to end.
      </p>
      <Link
        href="/troubleshoot"
        className={buttonVariants({ size: "lg", className: "mt-4 gap-2" })}
      >
        <FilePlus2 />
        Troubleshoot a case
      </Link>
    </div>
  );
}
