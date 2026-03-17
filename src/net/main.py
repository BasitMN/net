import typer
import subprocess
import ipaddress
import urllib.request
import time

app = typer.Typer(no_args_is_help=True)

def _get_mac(ip: str):
    result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, timeout=5)
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == ip:
            return parts[2]
    return None

def _get_vendor(mac_addr: str):
    url = f"https://api.macvendors.com/{mac_addr}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        elif e.code == 429:
            raise Exception("Too many requests. Please try again later.")
        else:
            raise Exception(f"HTTP {e.code} {e.reason}")
    except Exception as e:
        raise Exception(f"{e}")

def _is_raspberry_pi(vendor: str) -> bool:
    if vendor is None:
        return False
    return "raspberry" in vendor.lower()

@app.command()
def scan(netmask: str = typer.Argument(..., help="Netmask to scan (e.g., 192.168.1.0/27)")):
    """Scan network, find MACs, detect Raspberry Pis."""
    print(f"Scanning network: {netmask}...")
    try:
        network = ipaddress.ip_network(netmask, strict=False)
    except ValueError as e:
        print(f"Error: Invalid netmask '{netmask}'. {e}")
        raise typer.Exit(code=1)

    try:
        for ip in network:
            ip_str = str(ip)
            try:
                result = subprocess.run(
                    ["ping", "-n", "-c", "1", "-W", "1", ip_str],
                    capture_output=True, text=True, timeout=3,
                )
                if result.returncode != 0:
                    continue

                mac = _get_mac(ip_str)
                if mac is None:
                    continue

                try:
                    vendor = _get_vendor(mac)
                    time.sleep(1)
                except Exception as e:
                    typer.secho(f"Vendor lookup failed for {mac}: {e}", fg=typer.colors.YELLOW, err=True)
                    vendor = None

                if _is_raspberry_pi(vendor):
                    print(f"Yes, {mac} {ip_str} is a Raspberry Pi address.")
                else:
                    print(f"No, {mac} {ip_str} is not a known Raspberry Pi address.")

            except subprocess.TimeoutExpired:
                continue
            except KeyboardInterrupt:
                raise

    except KeyboardInterrupt:
        print("\nScan interrupted by user. Exiting...")
        raise typer.Exit(code=0)

@app.command()
def other():
    """Dummy command to avoid command name being collapsed."""
    pass

if __name__ == "__main__":
    app()
