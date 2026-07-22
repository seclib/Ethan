// Minimal safe barrel: only re-export confirmed-safe components.
// Fragile exports are intentionally omitted until their files are normalized.

export { Alert, AlertDescription, AlertTitle } from "./alert";
export { Button } from "./button";
export { Badge } from "./badge";
export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./card";
export { CommandPalette } from "./command-palette";
export type { CommandItem, CommandPaletteProps } from "./command-palette";
export { Dialog } from "./dialog";
export { Input } from "./input";
export { Progress } from "./progress";
export { Separator } from "./separator";
export { Skeleton } from "./skeleton";
export { Spinner } from "./spinner";
export { Switch } from "./switch";
export { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table";
export { Textarea } from "./textarea";
export { Tooltip } from "./tooltip";
// NOTE: additional tooltip/avatar variants are skipped from barrel for now