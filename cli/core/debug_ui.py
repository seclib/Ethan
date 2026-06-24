"""Debug UI — user-facing diagnosis and fix presentation."""
from cli.core import colors as clr


class DebugUI:
    """User-facing debug report."""

    @staticmethod
    def show_diagnosis(classification, recipe, can_auto_fix: bool) -> str:
        """Render diagnosis to user."""
        lines = [
            "",
            f"  {clr.C.YELLOW}⚕  Diagnosis{clr.C.RESET}",
            "",
            f"  Error: {clr.C.RED}{classification.code}{clr.C.RESET}",
            f"  Severity: {classification.severity}",
            f"  Category: {classification.category}",
            "",
            f"  {clr.C.CYAN}→ Suggestion:{clr.C.RESET} {recipe.suggestion}",
        ]

        if can_auto_fix and recipe.auto_patch:
            lines.extend(
                [
                    "",
                    f"  {clr.C.GREEN}✓ Auto-fix available:{clr.C.RESET} {recipe.auto_patch}",
                    f"  Applying automatically and retrying...",
                ]
            )

        return "\n".join(lines)

    @staticmethod
    def show_retry_result(result) -> str:
        """Show retry outcome."""
        if result.success:
            status = f"{clr.C.GREEN}✓ Command succeeded after fix{clr.C.RESET}"
        else:
            status = f"{clr.C.RED}✗ Command still failing{clr.C.RESET}"

        return (
            f""
            f"  {status}"
            f"  Attempts: {result.attempt}, Exit code: {result.exit_code}"
        )

    @staticmethod
    def show_manual_escalation(recipe) -> str:
        """Show manual intervention message."""
        lines = [
            "",
            f"  {clr.C.YELLOW}⚠  Manual intervention required{clr.C.RESET}",
            f"  {clr.C.DIM}{recipe.suggestion}{clr.C.RESET}",
            "",
        ]
        return "\n".join(lines)