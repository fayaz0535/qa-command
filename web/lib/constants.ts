// Mirrors api/config.py's DEFAULT_ADO_WIQL — shown as a starting point in the
// settings form. The backend falls back to this same value server-side if
// wiql_query is left empty, so this is display-only convenience, not a second
// source of truth the backend depends on.
export const DEFAULT_ADO_WIQL =
  "SELECT [System.Id] FROM WorkItems " +
  "WHERE [System.WorkItemType] = 'Bug' AND [System.State] <> 'Closed' " +
  "ORDER BY [System.CreatedDate] DESC";
