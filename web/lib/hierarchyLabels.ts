// The backend's ADO area-path parser (api/services/areapath_parser.py) uses the
// literal string "(none)" as a placeholder when a work item's Area Path doesn't
// have enough segments to fill Module/Sub-module — it's real data, not missing
// data, so every view must render it, just with a friendlier label than the
// raw placeholder.
export const UNASSIGNED_RAW = "(none)";

export function displayHierarchyName(name: string | null | undefined): string {
  if (!name || name === UNASSIGNED_RAW) return "Unassigned";
  return name;
}
