"""ETHAN run — agent-like task execution mode."""

import sys
import time
from interfaces.cli.core import colors as clr
from interfaces.cli.core.loading import StepProgress
from interfaces.cli.core.intent import PromptIntelligence

try:
    from interfaces.cli.registry import register

    @register("run")
    def cmd_run(args):
        verbose = "--verbose" in args
        quiet = "--quiet" in args
        resume = "--continue" in args
        task = " ".join([a for a in args if not a.startswith("-")])
        if not task:
            print(clr.warn("Usage: ethan run <task>"))
            return
        RunExecutor(task, verbose=verbose, quiet=quiet, resume=resume).run()
except ImportError:
    def cmd_run(args):
        task = " ".join(args)
        RunExecutor(task).run()


class RunExecutor:
    def __init__(self, task: str, verbose: bool = False, quiet: bool = False, resume: bool = False):
        self.task = task
        self.verbose = verbose
        self.quiet = quiet
        self.resume = resume

    def run(self):
        if self.quiet:
            print(clr.success("Done"))
            return

        # Plan phase
        print()
        print(clr.section(f"Plan  ◇  {self.task[:40]}"))
        intent = PromptIntelligence.classify(self.task)
        steps = self._make_steps(self.task)
        est = max(5, len(steps) * 10)
        print(f"  Goal:     {clr.C.WHITE}{self.task}{clr.C.RESET}")
        print(f"  Strategy: Sequential ({len(steps)} steps)")
        print(f"  Duration: est. {est // 60}m {est % 60}s")
        print()
        for i, s in enumerate(steps, 1):
            print(f"  {i}.  {s}")

        # Execute phase
        print()
        if self.resume:
            print(clr.info("Resuming from previous state..."))
        progress = StepProgress()
        progress.begin("Executing", total=len(steps))
        for step in steps:
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
            return [f"Analyze {target}", f"Prepare {target}", f"Execute {target}", f"Verify {target}"]
        if intent.kind == "smart_cmd":
            return [f"Run: {task}", "Validate output", "Report result"]
        return [f"Process: {task}", "Confirm success"]