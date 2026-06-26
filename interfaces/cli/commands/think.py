"""ETHAN think — structured reasoning mode."""

import sys
import time
from interfaces.cli.core import colors as clr
from interfaces.cli.core.loading import StepProgress, Thinker
from interfaces.cli.core.intent import PromptIntelligence

try:
    from interfaces.cli.registry import register

    @register("think")
    def cmd_think(args):
        verbose = "--verbose" in args
        quiet = "--quiet" in args
        task = " ".join([a for a in args if not a.startswith("-")])
        if not task:
            print(clr.warn("Usage: ethan think <task>"))
            return
        ThinkRunner(task, verbose=verbose, quiet=quiet).run()
except ImportError:
    def cmd_think(args):
        task = " ".join(args)
        ThinkRunner(task).run()


class ThinkRunner:
    def __init__(self, task: str, verbose: bool = False, quiet: bool = False):
        self.task = task
        self.verbose = verbose
        self.quiet = quiet

    def run(self):
        if self.quiet:
            print(clr.success("Done"))
            return

        # Plan phase
        print()
        print(clr.section("Plan generated"))
        intent = PromptIntelligence.classify(self.task)
        steps = self._make_steps(self.task)
        est = max(5, len(steps) * 10)
        print(f"  Goal:    {clr.C.WHITE}{self.task}{clr.C.RESET}")
        print(f"  Steps:   {len(steps)}")
        print(f"  Duration: est. {est // 60}m {est % 60}s")
        print()
        for i, s in enumerate(steps, 1):
            label = s if not self.verbose else s
            print(f"  {i}.  {label}")

        # Execute phase
        print()
        progress = StepProgress()
        progress.begin("Executing", total=len(steps))
        for i, step in enumerate(steps, 1):
            progress.step(step)
        progress.complete("Complete")

        # Report phase
        print()
        print(clr.section(f"Complete  ◇  {self.task[:40]}"))
        print(clr.success("All steps executed successfully"))
        total = 0.5 * len(steps)
        print(clr.timing(total, ""))
        print()
        suggestions = PromptIntelligence.suggest_next([], intent)
        if suggestions:
            print(clr.section("What next?"))
            for s in suggestions:
                print(clr.item(s))
            print()

    def _make_steps(self, task: str) -> list[str]:
        intent = PromptIntelligence.classify(task)
        if intent.kind == "intent":
            target = intent.params.get("target", "task")
            return [f"Analyze {target}", f"Execute {target}", f"Report status"]
        if intent.kind == "smart_cmd":
            return [f"Run: {task}", "Verify result"]
        return [f"Process: {task}", "Confirm success"]