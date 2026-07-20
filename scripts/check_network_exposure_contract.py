#!/usr/bin/env python3
"""Validate local bind, LAN exposure, and cleanup guidance (Issue #136)."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "chapter3": Path("docs/chapter3/index.md"),
    "chapter4": Path("docs/chapter4/index.md"),
}


class ContractError(RuntimeError):
    """Raised when the network exposure contract is incomplete or unsafe."""


@dataclass(frozen=True)
class Snapshot:
    files: Dict[str, str]


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise ContractError(f"{label}: missing {token!r}")


def reject(text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
        raise ContractError(f"{label}: forbidden pattern {pattern!r}")


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"{label} unreadable: {path}: {exc}") from exc


def load_source(root: Path = ROOT) -> Snapshot:
    return Snapshot({name: read_text(root / path, name) for name, path in TARGETS.items()})


def check_order(text: str, tokens: list[str], label: str) -> None:
    positions = []
    for token in tokens:
        require(text, token, label)
        positions.append(text.index(token))
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise ContractError(f"{label}: expected order is broken")


def check_source(snapshot: Snapshot, root: Path = ROOT, check_workflow: bool = True) -> None:
    chapter3 = snapshot.files["chapter3"]
    chapter4 = snapshot.files["chapter4"]
    combined = "\n".join(snapshot.files.values())

    nginx_section = chapter3[chapter3.index("## 3.4 実践: Web サーバーの導入と管理") :]
    check_order(
        nginx_section,
        [
            "if [ -e /usr/sbin/policy-rc.d ]; then",
            "trap cleanup_policy_rcd EXIT",
            "'exit 101'",
            "if ! sudo apt install nginx -y; then",
            "Nginx installation failed; temporary policy will be removed",
            "cleanup_policy_rcd\ntrap - EXIT",
            "#### Nginx install Source Note（確認日: 2026-07-20）",
            "https://manpages.debian.org/bookworm/init-system-helpers/invoke-rc.d.8.en.html",
            "listen 127.0.0.1:80;",
            "location = /nginx_status",
            "sudo rm -f /etc/nginx/sites-enabled/default",
            "if systemctl is-active --quiet nginx; then",
            "sudo systemctl reload nginx",
            "sudo systemctl start nginx",
            'ListenerOutput=$(sudo ss -H -ltn \'( sport = :80 )\')',
            "Unexpected non-loopback Nginx listener remains",
            "curl --fail http://127.0.0.1/nginx_status",
        ],
        "chapter 3 Nginx install and enabled-site flow",
    )
    for token in [
        "既存policyがある環境では上書きせず",
        "終了status 101を返すとservice actionをpolicyにより拒否",
        "if ! sudo apt install nginx -y; then",
        "Nginx installation failed; temporary policy will be removed",
        "systemctl is-active nginx",
        "listen 127.0.0.1:80;",
        "sudo rm -f /etc/nginx/sites-enabled/default",
        "if systemctl is-active --quiet nginx; then",
        "sudo systemctl reload nginx",
        "sudo systemctl start nginx",
        'ListenerOutput=$(sudo ss -H -ltn \'( sport = :80 )\')',
        'Expected Nginx to listen on 127.0.0.1:80',
        'if awk \'$4 != "127.0.0.1:80"',
        'Unexpected non-loopback Nginx listener remains',
        "curl --fail http://127.0.0.1/",
        "../chapter4/#wsl-lan-publication",
    ]:
        require(chapter3, token, "chapter 3 local Nginx")
    for pattern in [
        r"^\s*listen\s+80;\s*$",
        r"^\s*listen\s+\[::\]:80;\s*$",
        r"sites-available/default",
    ]:
        reject(chapter3, pattern, "chapter 3 wildcard Nginx")

    check_order(
        chapter4,
        [
            "### local確認（既定・推奨）",
            "python3 -m http.server --bind 127.0.0.1 8000",
            "Test-NetConnection -ComputerName localhost -Port 8000",
            "### LAN公開runbook（必要な場合だけ）",
            "{: #wsl-lan-publication}",
            "python3 -m http.server --bind 0.0.0.0 8080",
            "#### NAT方式: portproxyとWindows Firewallを対で管理",
            '$RuleName = "WSL2-Lab-NAT-TCP-8080"',
            "NAT AllowedRemote must be exactly one dotted-decimal IPv4 address",
            "$PortProxyRows = netsh interface portproxy show v4tov4",
            'if ($ExistingProxy) { throw "The listen address and port already have a portproxy entry" }',
            "netsh interface portproxy add v4tov4",
            'if ($LASTEXITCODE -ne 0) { throw "Failed to create portproxy; Firewall rule was not created" }',
            "New-NetFirewallRule @FirewallParams",
            "# 先に受信許可を閉じ、次に同じlisten addressのportproxyを削除\n"
            "Remove-NetFirewallRule -Name $RuleName -ErrorAction Stop\n"
            "netsh interface portproxy delete v4tov4",
            "#### mirrored mode: Hyper-V Firewall ruleを個別管理",
            '$HvRuleName = "WSL2-Lab-Mirrored-TCP-8080"',
            "Mirrored AllowedRemote must be exactly one dotted-decimal IPv4 address",
            "New-NetFirewallHyperVRule @HvFirewallParams",
            "Remove-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction Stop",
            "#### Network Exposure Source Notes（確認日: 2026-07-20）",
        ],
        "chapter 4 exposure decision flow",
    )

    for token in [
        "local確認ではportproxyやFirewall許可ruleを追加しません",
        "Windowsの特定LAN IPv4へのportproxy",
        "portproxyは作成しない",
        'if ($ListenAddress -eq "0.0.0.0") { throw "Use one Windows LAN IPv4" }',
        "[System.Net.IPAddress]::TryParse($AllowedRemote, [ref]$NatAllowedRemoteAddress)",
        "$NatAllowedRemoteAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork",
        "$NatAllowedRemoteAddress.ToString() -cne $AllowedRemote",
        "Get-NetConnectionProfile -InterfaceIndex $ListenInterface.InterfaceIndex -ErrorAction Stop",
        'if ($ListenProfile.NetworkCategory -ne "Private") { throw "The listen interface must use the Private profile" }',
        'Get-NetFirewallRule -Name $RuleName -ErrorAction SilentlyContinue) { throw "RuleName already exists"',
        '$ExistingProxy = $PortProxyRows | Select-String -Pattern "^\\s*$([regex]::Escape($ListenAddress))\\s+$ListenPort\\s+"',
        "Name = $RuleName",
        "LocalAddress = $ListenAddress",
        "LocalPort = $ListenPort",
        "RemoteAddress = $AllowedRemote",
        'Profile = "Private"',
        "Get-NetFirewallAddressFilter",
        'if ($LASTEXITCODE -ne 0) { Write-Error "Firewall rule creation and portproxy rollback both failed" }',
        'if ($LASTEXITCODE -ne 0) { throw "Failed to remove the portproxy entry" }',
        "Get-NetFirewallRule -Name $RuleName -ErrorAction SilentlyContinue",
        "削除後の`TcpTestSucceeded`は`False`",
        '$WslVmCreatorId = "{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}"',
        "[System.Net.IPAddress]::TryParse($AllowedRemote, [ref]$HvAllowedRemoteAddress)",
        "$HvAllowedRemoteAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork",
        "$HvAllowedRemoteAddress.ToString() -cne $AllowedRemote",
        "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -VMCreatorId $WslVmCreatorId",
        "Get-NetFirewallHyperVProfile -PolicyStore ActiveStore",
        'Get-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction SilentlyContinue) { throw "RuleName already exists"',
        "Name = $HvRuleName",
        "VMCreatorId = $WslVmCreatorId",
        "LocalPorts = 8080",
        "RemoteAddresses = $AllowedRemote",
        'Profiles = "Private"',
        "Get-NetFirewallHyperVRule -PolicyStore ActiveStore -Name $HvRuleName",
        "Get-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction SilentlyContinue",
        "引数なしの`Remove-NetFirewallHyperVRule`は全ruleを削除し得る",
        "組織ポリシー",
        "https://learn.microsoft.com/en-us/windows/wsl/networking",
        "windows-firewall/hyper-v-firewall",
        "powershell/module/netsecurity/new-netfirewallrule",
        "powershell/module/netsecurity/remove-netfirewallrule",
        "powershell/module/netsecurity/new-netfirewallhypervrule",
        "powershell/module/netsecurity/remove-netfirewallhypervrule",
        "powershell/module/netsecurity/get-netfirewallhypervvmsetting",
        "https://nginx.org/en/docs/http/ngx_http_core_module.html#listen",
        "https://docs.python.org/3/library/http.server.html#cmdoption-http-server-bind",
        "https://nodejs.org/api/net.html#serverlisten",
    ]:
        require(chapter4, token, "chapter 4 protected exposure")

    for token in [
        "python3 -m http.server --bind 127.0.0.1 --cgi 8000",
        "server.listen(3000, '127.0.0.1', () => {",
        "ss -ltnp '( sport = :3000 )'",
        "nc -l 127.0.0.1 12345",
        'python3 -m http.server --bind 127.0.0.1 "$port"',
        'HTTPServer(("127.0.0.1", 8000), Handler)',
    ]:
        require(chapter4, token, "chapter 4 local server examples")

    for pattern in [
        r"^\s*python3\s+-m\s+http\.server(?![^\n]*--bind)[^\n]*$",
        r"server\.listen\(3000\s*,\s*\(\)\s*=>",
        r"^\s*nc\s+-l(?![^\n]*127\.0\.0\.1)[^\n]*$",
        r"listenaddress=0\.0\.0\.0",
        r"\$ListenAddress\s*=\s*[\"']0\.0\.0\.0[\"']",
        r"^\s*New-NetFirewallRule\s+-DisplayName",
        r"(?:RemoteAddress|RemoteAddresses|Profile|Profiles)\s*=\s*[\"'](?:Any|Public)[\"']",
        r"^\s*Remove-NetFirewallRule\s*$",
        r"^\s*Remove-NetFirewallHyperVRule\s*$",
        r"Get-NetFirewallHyperVVMSetting[^\n]*\s-Name\s+\$WslVmCreatorId",
    ]:
        reject(combined, pattern, "unsafe network guidance")

    if check_workflow:
        workflow = read_text(root / ".github/workflows/book-qa.yml", "Book QA workflow")
        package = read_text(root / "package.json", "package.json")
        for token in [
            "python3 scripts/check_network_exposure_contract.py --self-test",
            "python3 scripts/check_network_exposure_contract.py",
            "python3 scripts/check_network_exposure_contract.py --runtime-test",
            "python3 scripts/check_network_exposure_contract.py --built-site _site",
        ]:
            require(workflow, token, "Book QA workflow")
        require(package, '"check:network-exposure"', "npm test network contract")
        require(package, "npm run check:network-exposure", "npm test network contract")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def visible_text(document: str) -> str:
    parser = TextExtractor()
    parser.feed(document)
    parser.close()
    text = html.unescape("".join(parser.parts))
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def load_built(site: Path) -> Snapshot:
    paths = {
        "chapter3": site / "chapter3/index.html",
        "chapter4": site / "chapter4/index.html",
    }
    return Snapshot({name: read_text(path, f"built {name}") for name, path in paths.items()})


def check_built(snapshot: Snapshot) -> None:
    chapter3_html = snapshot.files["chapter3"]
    chapter4_html = snapshot.files["chapter4"]
    chapter3 = visible_text(chapter3_html)
    chapter4 = visible_text(chapter4_html)
    for token in [
        'href="../chapter4/#wsl-lan-publication"',
        "policy-rc.d",
        "Nginx install Source Note（確認日: 2026-07-20）",
        "https://manpages.debian.org/bookworm/init-system-helpers/invoke-rc.d.8.en.html",
        "listen 127.0.0.1:80;",
        "sudo systemctl reload nginx",
        "ListenerOutput=$(sudo ss -H -ltn '( sport = :80 )')",
        "Expected Nginx to listen on 127.0.0.1:80",
        'if awk \'$4 != "127.0.0.1:80"',
        "Unexpected non-loopback Nginx listener remains",
        "location = /nginx_status",
        "curl --fail http://127.0.0.1/nginx_status",
    ]:
        require(
            chapter3_html if token.startswith(("href=", "https://")) else chapter3,
            token,
            "built chapter 3",
        )
    for token in [
        'id="wsl-lan-publication"',
        "python3 -m http.server --bind 127.0.0.1 8000",
        "server.listen(3000, '127.0.0.1', () => {",
        "python3 -m http.server --bind 0.0.0.0 8080",
        "WSL2-Lab-NAT-TCP-8080",
        "The listen address and port already have a portproxy entry",
        "Failed to create portproxy; Firewall rule was not created",
        "NAT AllowedRemote must be exactly one dotted-decimal IPv4 address",
        "RemoteAddress = $AllowedRemote",
        'Profile = "Private"',
        "Remove-NetFirewallRule -Name $RuleName -ErrorAction Stop",
        "netsh interface portproxy delete v4tov4",
        "WSL2-Lab-Mirrored-TCP-8080",
        "Mirrored AllowedRemote must be exactly one dotted-decimal IPv4 address",
        "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -VMCreatorId $WslVmCreatorId",
        "RemoteAddresses = $AllowedRemote",
        'Profiles = "Private"',
        "Remove-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction Stop",
        "Network Exposure Source Notes（確認日: 2026-07-20）",
    ]:
        require(chapter4_html if token.startswith("id=") else chapter4, token, "built chapter 4")
    combined = chapter3 + "\n" + chapter4
    for pattern in [
        r"^\s*listen\s+80;\s*$",
        r"^\s*listen\s+\[::\]:80;\s*$",
        r"sites-available/default",
        r"^\s*python3\s+-m\s+http\.server(?![^\n]*--bind)[^\n]*$",
        r"server\.listen\(3000\s*,\s*\(\)\s*=>",
        r"^\s*nc\s+-l(?![^\n]*127\.0\.0\.1)[^\n]*$",
        r"listenaddress=0\.0\.0\.0",
        r"^\s*New-NetFirewallRule\s+-DisplayName",
        r"(?:RemoteAddress|RemoteAddresses|Profile|Profiles)\s*=\s*[\"'](?:Any|Public)[\"']",
        r"^\s*Remove-NetFirewallRule\s*$",
        r"^\s*Remove-NetFirewallHyperVRule\s*$",
        r"Get-NetFirewallHyperVVMSetting[^\n]*\s-Name\s+\$WslVmCreatorId",
    ]:
        reject(combined, pattern, "built unsafe network guidance")
    print("Built WSL network exposure contract passed (2 pages).")


def runtime_test() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as selector:
        selector.bind(("127.0.0.1", 0))
        port = selector.getsockname()[1]
    command = [
        sys.executable,
        "-m",
        "http.server",
        "--bind",
        "127.0.0.1",
        str(port),
        "--directory",
        str(ROOT / "docs"),
    ]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 10
        while True:
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else ""
                raise ContractError(f"loopback runtime server exited early: {stderr.strip()}")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                    if response.status != 200:
                        raise ContractError(f"loopback runtime returned HTTP {response.status}")
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise ContractError("loopback runtime server did not become ready")
                time.sleep(0.1)

        if shutil.which("ss"):
            result = subprocess.run(
                ["ss", "-ltn", f"( sport = :{port} )"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0 or f"127.0.0.1:{port}" not in result.stdout:
                raise ContractError("runtime ss output does not show the loopback listener")
            if f"0.0.0.0:{port}" in result.stdout or f"[::]:{port}" in result.stdout:
                raise ContractError("runtime server unexpectedly has a wildcard listener")

        non_loopback_addresses: set[str] = set()
        if shutil.which("ip"):
            try:
                addresses = subprocess.run(
                    ["ip", "-j", "-4", "addr", "show", "scope", "global"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if addresses.returncode == 0:
                    for interface in json.loads(addresses.stdout or "[]"):
                        for address in interface.get("addr_info", []):
                            local = address.get("local", "")
                            if address.get("family") == "inet" and local and not local.startswith("127."):
                                non_loopback_addresses.add(local)
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
                pass
        if not non_loopback_addresses:
            try:
                for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                    local = result[4][0]
                    if local and not local.startswith("127."):
                        non_loopback_addresses.add(local)
            except OSError:
                pass

        for non_loopback in sorted(non_loopback_addresses):
            try:
                with socket.create_connection((non_loopback, port), timeout=1):
                    pass
            except OSError:
                continue
            raise ContractError(
                f"loopback runtime server is reachable through non-loopback address {non_loopback}"
            )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    scope_result = (
        f"non-loopback rejection on {len(non_loopback_addresses)} address(es)"
        if non_loopback_addresses
        else "non-loopback probe skipped: no local address available"
    )
    print(f"WSL network runtime contract passed (loopback HTTP 200, listener scope, {scope_result}).")


def expect_failure(label: str, action, expected: str) -> None:
    try:
        action()
    except ContractError as exc:
        if expected in str(exc):
            return
        raise ContractError(f"self-test {label}: wrong error: {exc}") from exc
    raise ContractError(f"self-test {label}: mutation was accepted")


def self_test() -> None:
    baseline = load_source()
    check_source(baseline)

    def replaced(name: str, old: str, new: str) -> Snapshot:
        files = dict(baseline.files)
        if old not in files[name]:
            raise ContractError(f"self-test fixture missing: {name}: {old!r}")
        files[name] = files[name].replace(old, new, 1)
        return Snapshot(files)

    cases = [
        (
            "missing install suppression",
            "chapter3",
            "trap cleanup_policy_rcd EXIT",
            "# package may start here",
            "install and enabled-site flow",
        ),
        (
            "disabled status site",
            "chapter3",
            "location = /nginx_status",
            "# status endpoint omitted",
            "install and enabled-site flow",
        ),
        (
            "missing install failure exit",
            "chapter3",
            "Nginx installation failed; temporary policy will be removed",
            "# install failure ignored",
            "install and enabled-site flow",
        ),
        (
            "missing active-service reload",
            "chapter3",
            "    sudo systemctl reload nginx",
            "    # active process keeps its old configuration",
            "install and enabled-site flow",
        ),
        (
            "specific LAN listener accepted",
            "chapter3",
            'if awk \'$4 != "127.0.0.1:80"',
            'if awk \'$4 ~ /^(0\\.0\\.0\\.0|\\*|\\[::\\]):80$/',
            "local Nginx",
        ),
        (
            "missing listener failure",
            "chapter3",
            "Unexpected non-loopback Nginx listener remains",
            "# non-loopback listener only displayed",
            "install and enabled-site flow",
        ),
        (
            "Nginx wildcard",
            "chapter3",
            "listen 127.0.0.1:80;",
            "listen 80;",
            "install and enabled-site flow",
        ),
        (
            "Python host omitted",
            "chapter4",
            "python3 -m http.server --bind 127.0.0.1 8000",
            "python3 -m http.server 8000",
            "decision flow",
        ),
        (
            "Node host omitted",
            "chapter4",
            "server.listen(3000, '127.0.0.1', () => {",
            "server.listen(3000, () => {",
            "local server examples",
        ),
        ("missing remote address", "chapter4", "RemoteAddress = $AllowedRemote", "RemotePort = 443", "protected exposure"),
        ("broad Windows profile", "chapter4", 'Profile = "Private"', 'Profile = "Any"', "protected exposure"),
        (
            "missing NAT single-client validation",
            "chapter4",
            "NAT AllowedRemote must be exactly one dotted-decimal IPv4 address",
            "# NAT remote scope not validated",
            "decision flow",
        ),
        (
            "wrong Hyper-V VM setting parameter",
            "chapter4",
            "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -VMCreatorId $WslVmCreatorId",
            "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -Name $WslVmCreatorId",
            "protected exposure",
        ),
        (
            "missing mirrored single-client validation",
            "chapter4",
            "Mirrored AllowedRemote must be exactly one dotted-decimal IPv4 address",
            "# mirrored remote scope not validated",
            "decision flow",
        ),
        (
            "missing existing portproxy guard",
            "chapter4",
            'if ($ExistingProxy) { throw "The listen address and port already have a portproxy entry" }',
            "# existing endpoint not checked",
            "decision flow",
        ),
        (
            "missing portproxy add failure guard",
            "chapter4",
            'if ($LASTEXITCODE -ne 0) { throw "Failed to create portproxy; Firewall rule was not created" }',
            "# failed native command ignored",
            "decision flow",
        ),
        (
            "missing Windows rule cleanup",
            "chapter4",
            "Remove-NetFirewallRule -Name $RuleName -ErrorAction Stop",
            "Disable-NetFirewallRule -Name $RuleName",
            "decision flow",
        ),
        (
            "missing portproxy cleanup",
            "chapter4",
            "# 先に受信許可を閉じ、次に同じlisten addressのportproxyを削除\n"
            "Remove-NetFirewallRule -Name $RuleName -ErrorAction Stop\n"
            "netsh interface portproxy delete v4tov4",
            "# 受信許可だけを閉じ、portproxyは残す\n"
            "Remove-NetFirewallRule -Name $RuleName -ErrorAction Stop\n"
            "netsh interface portproxy show v4tov4",
            "decision flow",
        ),
        (
            "wildcard Windows listen",
            "chapter4",
            "$ListenAddress = Read-Host \"Windows LAN IPv4 (not 0.0.0.0)\"",
            '$ListenAddress = "0.0.0.0"',
            "unsafe network guidance",
        ),
        (
            "missing Hyper-V remote address",
            "chapter4",
            "RemoteAddresses = $AllowedRemote",
            "RemotePorts = 443",
            "protected exposure",
        ),
        (
            "broad Hyper-V profile",
            "chapter4",
            'Profiles = "Private"',
            'Profiles = "Public"',
            "protected exposure",
        ),
        (
            "missing Hyper-V cleanup",
            "chapter4",
            "Remove-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction Stop",
            "Disable-NetFirewallHyperVRule -Name $HvRuleName",
            "decision flow",
        ),
        (
            "stale source note",
            "chapter4",
            "Network Exposure Source Notes（確認日: 2026-07-20）",
            "Network Exposure Source Notes（確認日なし）",
            "decision flow",
        ),
    ]
    for label, name, old, new, expected in cases:
        expect_failure(
            label,
            lambda n=name, o=old, v=new: check_source(replaced(n, o, v), check_workflow=False),
            expected,
        )
    print(f"WSL network exposure contract self-test passed ({len(cases)} negative mutations).")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--built-site", type=Path)
    parser.add_argument("--runtime-test", action="store_true")
    args = parser.parse_args()
    modes = sum([args.self_test, args.built_site is not None, args.runtime_test])
    if modes > 1:
        raise ContractError("choose one of --self-test, --built-site, or --runtime-test")
    if args.self_test:
        self_test()
    elif args.built_site is not None:
        check_built(load_built(args.built_site.resolve()))
    elif args.runtime_test:
        runtime_test()
    else:
        check_source(load_source())
        print("WSL network exposure source contract passed (2 pages).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"WSL network exposure contract failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
