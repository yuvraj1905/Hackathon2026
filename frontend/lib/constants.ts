/**
 * Build options: what the client wants to build.
 * Used in the estimation form multi-select and sent to the API.
 */
export const BUILD_OPTION_VALUES = [
  "mobile",
  "web",
  "design",
  "backend",
  "admin",
] as const;

export type BuildOption = (typeof BUILD_OPTION_VALUES)[number];

/** Human-readable labels for build options (for display in UI) */
export const BUILD_OPTION_LABELS: Record<BuildOption, string> = {
  mobile: "Mobile App",
  web: "Web App",
  design: "Design",
  backend: "Backend",
  admin: "Admin",
};
