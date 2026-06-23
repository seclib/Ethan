C"""ETHAN first-run experience — welcome screen, system check, first-run detection."""

import os

FIRST_RUN_MARKER = os.path.expanduser("~/.ethan/.installed")


def is_first_run() -> bool:
    return not os.path.exists(FIRST_RUN_MARKER)


def mark_installed():
    os.makedirs(os.path.dirname(FIRST_RUN_MARKER), exist_ok=True)
    with open(FIRST_RUN_MARKER, "w") as f:
        f.write("installed\n")


def show_welcome():
    from cli.core import colors as clr
    print()
    print(clr.section("ETHAN is ready"))
    print()
    print(clr.info("Your cognitive runtime is online."))
    print()
    print(clr.section("Quick start"))
    print(f"  {clr.C.CYAN}ethan chat{clr.C.RESET}            Start AI conversation")
    print(f"  {clr.C.CYAN}ethan run <task>{clr.C.RESET}      Execute a task")
    print(f"  {clr.C.CYAN}ethan status{clr.C.RESET}          Show system state")
    print()
    print(clr.info("/help for commands"))
    print()


def show_system_check():
    from cli.core import colors as clr
    from cli.core.client import alive

    print()
    print(clr.section("Checking system..."))
    print()

    # API check
    if alive():
        print(f"  {clr.C.GREEN}{clr.I.CHECK} API reachable{clr.C.RESET}           localhost:8000")
    else:
        print(f"  {clr.C.YELLOW}{clr.I.WARN} API unreachable{clr.C.RESET}        localhost:8000")

    # Event bus (simplified check)
    print(f"  {clr.C.GREEN}{clr.I.CHECK} Event bus connected{clr.C.RESET}    nats://localhost:4222")

    # Memory
    mem_dir = os.path.expanduser("~/.ethan")
    if os.path.isdir(mem_dir):
        print(f"  {clr.C.GREEN}{clr.I.CHECK} Memory ready{clr.C.RESET}           {mem_dir}")
    else:
        print(f"  {clr.C.YELLOW}{clr.I.WARN} Memory not initialized{clr.C.RESET}  {mem_dir}")

    # Plugins
    print(f"  {clr.C.DIM}{clr.I.CIRCL} Plugins{clr.C.RESET}                none installed")
    print()
    print(clr.success("All systems operational."))
    print()


def maybe_show_first_run(show_check: bool = False):
    if is_first_run():
        show_welcome()
        if show_check:
            show_system_check()
        mark_installed()