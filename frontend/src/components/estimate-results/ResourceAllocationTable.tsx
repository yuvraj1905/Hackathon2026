"use client";

import { Users } from "lucide-react";
import type { ResourceRow } from "@/lib/utils";
import { fmtNum } from "@/lib/utils";

interface ResourceAllocationTableProps {
  resources: ResourceRow[];
}

export function ResourceAllocationTable({ resources }: ResourceAllocationTableProps) {
  if (resources.length === 0) return null;

  return (
    <div>
      <div className="section-title">
        <h2>
          <Users className="mr-2 inline h-5 w-5 text-primary" />
          Resource Allocation
        </h2>
        <span className="line" />
      </div>
      <div className="card-spotlight table-premium overflow-hidden rounded-2xl">
        <table className="estimation-table">
          <thead>
            <tr>
              <th>Role</th>
              <th className="text-center">Senior</th>
              <th className="text-center">Mid</th>
              <th className="text-center">Junior</th>
              <th className="text-center font-bold text-primary">Total</th>
            </tr>
          </thead>
          <tbody>
            {resources.map((r) => (
              <tr key={r.role}>
                <td className="font-medium capitalize">{r.role.replace(/_/g, " ")}</td>
                <td className="text-center font-mono">{fmtNum(r.senior)}</td>
                <td className="text-center font-mono">{fmtNum(r.mid)}</td>
                <td className="text-center font-mono">{fmtNum(r.junior)}</td>
                <td className="text-center font-mono font-bold text-primary">{fmtNum(r.total)}</td>
              </tr>
            ))}
            <tr className="font-bold" style={{ background: "hsl(var(--muted) / 0.4)" }}>
              <td>Total Team</td>
              <td className="text-center font-mono">{fmtNum(resources.reduce((a, r) => a + r.senior, 0))}</td>
              <td className="text-center font-mono">{fmtNum(resources.reduce((a, r) => a + r.mid, 0))}</td>
              <td className="text-center font-mono">{fmtNum(resources.reduce((a, r) => a + r.junior, 0))}</td>
              <td className="text-center font-mono text-primary">{fmtNum(resources.reduce((a, r) => a + r.total, 0))}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
