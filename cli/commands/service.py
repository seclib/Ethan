"""ETHAN service — systemd service management."""
import subprocess
import sys
from registry import register

SERVICE_NAME = "ethan"


def _systemctl(args, user=True, check=True):
    cmd = ["systemctl"]
    if user:
        cmd.append("--user")
    cmd.extend(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


@register("service")
def cmd_service(args):
    if not args or args[0] not in ("start", "stop", "restart", "status"):
        print("usage: ethan service <start|stop|restart|status>")
        return 1
    sub = args[0]

    # Try user service first, fall back to system service
    rc, out, err = _systemctl([sub, SERVICE_NAME + ".service"], user=True, check=False)

    # If user service not found, try system service
    if "could not be found" in err or "not-found" in err:
        rc, out, err = _systemctl([sub, SERVICE_NAME + ".service"], user=False, check=False)

    if sub == "status":
        print(out)
        if err:
            print(err, file=sys.stderr)
    else:
        if rc == 0:
            print(f"Service {sub} succeeded.")
        else:
            print(f"Service {sub} failed: {err.strip()}", file=sys.stderr)
            return 1
    return 0