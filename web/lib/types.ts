export type Health = "red" | "amber" | "green";

export interface NodeMetrics {
  execution_pct: number;
  pass_rate: number;
  total_tests: number;
  open_defects: number;
  closed_defects: number;
  open_by_severity: Record<string, number>;
  aging_gt7: number;
  aging_gt14: number;
  aging_gt21: number;
  avg_resolution_days: number | null;
  defects_by_owner: Record<string, number>;
  health: Health;
}

export interface SubModuleNode {
  name: string;
  metrics: NodeMetrics;
}

export interface ModuleNode {
  name: string;
  metrics: NodeMetrics;
  sub_modules: Record<string, SubModuleNode>;
}

export interface PlatformNode {
  name: string;
  metrics: NodeMetrics;
  modules: Record<string, ModuleNode>;
}

export interface MetricsTree {
  metrics: NodeMetrics;
  platforms: Record<string, PlatformNode>;
}

export interface Defect {
  id: string;
  external_id: string;
  source: string;
  platform: string | null;
  module: string | null;
  sub_module: string | null;
  title: string;
  severity: "Critical" | "High" | "Medium" | "Low" | "TBC";
  state: string;
  owner_vendor: string | null;
  vendor_needs_review: boolean;
  assignee_email: string | null;
  raised_date: string | null;
  eta: string | null;
  aging_days: number | null;
  resolved_date: string | null;
  is_reopen: boolean;
  remarks: string;
}

export interface TestCase {
  id: string;
  external_id: string;
  source: string;
  platform: string | null;
  module: string | null;
  sub_module: string | null;
  title: string;
  status: "Passed" | "Failed" | "Blocked" | "Not Run" | "In Progress";
  phase: "SIT" | "UAT" | "BVT" | "Parallel Run" | null;
  executed_date: string | null;
}

export interface Insight {
  progress: string;
  risk: string;
  ask: string;
  generated: boolean;
  generated_at: string;
}

export interface HierarchyModule {
  name: string;
  sub_modules: string[];
}

export interface HierarchyPlatform {
  name: string;
  modules: HierarchyModule[];
}

export interface HierarchyTree {
  platforms: HierarchyPlatform[];
}

export interface TrendPoint {
  date: string;
  open_defects: number;
  closed_defects: number;
  execution_pct: number;
  pass_rate: number;
}

export interface Filters {
  platform?: string;
  module?: string;
  sub_module?: string;
  severity?: string;
  owner?: string;
  phase?: string;
  state?: string;
}

export interface EmailDraft {
  subject: string;
  html: string;
  key_message: string;
  risk: string;
  ask: string;
  attachments: Record<string, string>;
  dashboard_url: string;
  generated_at: string;
  reviewed_by_dm: boolean;
}
