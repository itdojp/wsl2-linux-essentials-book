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


def section_between(text: str, start: str, end: str, label: str) -> str:
    """Return a required, non-empty section bounded by two headings."""
    require(text, start, label)
    require(text, end, label)
    start_index = text.index(start)
    end_index = text.index(end, start_index + len(start))
    if end_index <= start_index:
        raise ContractError(f"{label}: section boundary order is broken")
    return text[start_index:end_index]


def check_source(snapshot: Snapshot, root: Path = ROOT, check_workflow: bool = True) -> None:
    chapter3 = snapshot.files["chapter3"]
    chapter4 = snapshot.files["chapter4"]
    combined = "\n".join(snapshot.files.values())

    nginx_section = chapter3[chapter3.index("## 3.4 実践: Web サーバーの導入と管理") :]
    check_order(
        nginx_section,
        [
            "if [ -e /usr/sbin/policy-rc.d ] || [ -L /usr/sbin/policy-rc.d ]; then",
            "trap cleanup_policy_rcd EXIT",
            "'exit 101'",
            "if ! sudo chmod 0755 /usr/sbin/policy-rc.d; then",
            "if ! sudo apt install nginx -y; then",
            "Nginx installation failed; temporary policy will be removed",
            "if ! cleanup_policy_rcd; then",
            "trap - EXIT",
            "#### Nginx install Source Note（確認日: 2026-07-20）",
            "https://manpages.debian.org/bookworm/init-system-helpers/invoke-rc.d.8.en.html",
            "listen 127.0.0.1:80;",
            "location = /nginx_status",
            "stop_nginx_fail_closed() {",
            "if ! sudo ln -sfn /etc/nginx/sites-available/mysite /etc/nginx/sites-enabled/mysite; then",
            "if ! sudo rm -f /etc/nginx/sites-enabled/default; then",
            "if ! sudo nginx -t; then",
            "if systemctl is-active --quiet nginx; then",
            "if ! sudo systemctl reload nginx; then",
            "if ! sudo systemctl start nginx; then",
            "Nginx is not active after applying the configuration",
            "if ! ListenerOutput=$(sudo ss -H -ltn '( sport = :80 )'); then",
            "Unexpected non-loopback Nginx listener remains",
            "curl --fail http://127.0.0.1/nginx_status",
        ],
        "chapter 3 Nginx install and enabled-site flow",
    )
    for token in [
        "既存policyがある環境では上書きせず",
        "if [ -e /usr/sbin/policy-rc.d ] || [ -L /usr/sbin/policy-rc.d ]; then",
        "終了status 101を返すとservice actionをpolicyにより拒否",
        "if ! sudo apt install nginx -y; then",
        "Nginx installation failed; temporary policy will be removed",
        "if ! printf '%s\\n' '#!/bin/sh' 'exit 101' | sudo tee /usr/sbin/policy-rc.d >/dev/null; then",
        'echo "Failed to write temporary /usr/sbin/policy-rc.d; abort before apt install" >&2',
        "if ! sudo chmod 0755 /usr/sbin/policy-rc.d; then",
        'echo "Failed to make temporary /usr/sbin/policy-rc.d executable; abort before apt install" >&2',
        "if ! cleanup_policy_rcd; then",
        'echo "Temporary policy cleanup failed; stop before configuring Nginx" >&2',
        "systemctl is-active nginx",
        "listen 127.0.0.1:80;",
        "stop_nginx_fail_closed() {",
        'echo "Failed to stop Nginx; disconnect from the network and stop it manually" >&2',
        "if ! sudo ln -sfn /etc/nginx/sites-available/mysite /etc/nginx/sites-enabled/mysite; then",
        'echo "Failed to enable the mysite configuration" >&2\n    stop_nginx_fail_closed\n    exit 1',
        "if ! sudo rm -f /etc/nginx/sites-enabled/default; then",
        'echo "Failed to disable the package-default Nginx site" >&2\n    stop_nginx_fail_closed\n    exit 1',
        "if ! sudo nginx -t; then",
        'echo "Nginx configuration test failed" >&2\n    stop_nginx_fail_closed\n    exit 1',
        "if systemctl is-active --quiet nginx; then",
        "if ! sudo systemctl reload nginx; then",
        'echo "Failed to reload Nginx" >&2\n        stop_nginx_fail_closed\n        exit 1',
        "if ! sudo systemctl start nginx; then",
        'echo "Failed to start Nginx" >&2\n        stop_nginx_fail_closed\n        exit 1',
        "if ! systemctl is-active --quiet nginx; then",
        'echo "Nginx is not active after applying the configuration" >&2\n    stop_nginx_fail_closed\n    exit 1',
        "if ! ListenerOutput=$(sudo ss -H -ltn '( sport = :80 )'); then",
        'echo "Failed to inspect the port 80 listener" >&2\n    stop_nginx_fail_closed\n    exit 1',
        'Expected Nginx to listen on 127.0.0.1:80',
        'echo "Expected Nginx to listen on 127.0.0.1:80" >&2\n    stop_nginx_fail_closed\n    exit 1',
        'if awk \'$4 != "127.0.0.1:80"',
        'Unexpected non-loopback Nginx listener remains',
        'echo "Unexpected non-loopback Nginx listener remains" >&2\n    stop_nginx_fail_closed\n    exit 1',
        "curl --fail http://127.0.0.1/",
        "設定test・reload/start・active状態・待受取得のいずれかが失敗",
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
            "Firewall設定前にwildcard serverを起動してはいけません",
            "#### NAT方式: portproxyとWindows Firewallを対で管理",
            '$RuleName = "WSL2-Lab-NAT-TCP-8080"',
            '$BlockRuleName = "WSL2-Lab-NAT-TCP-8080-Block-Others"',
            "NAT AllowedRemote must be exactly one dotted-decimal IPv4 address",
            "$PortProxyRows = netsh interface portproxy show v4tov4",
            'if ($ExistingProxy) { throw "The listen address and port already have a portproxy entry" }',
            "New-NetFirewallRule @BlockFirewallParams",
            "New-NetFirewallRule @FirewallParams",
            "netsh interface portproxy add v4tov4",
            "Portproxy rollback could not be verified; Firewall rules were retained",
            "#### mirrored mode: Hyper-V Firewall ruleを個別管理",
            '$HvRuleName = "WSL2-Lab-Mirrored-TCP-8080"',
            '$HvBlockRuleName = "WSL2-Lab-Mirrored-TCP-8080-Block-Others"',
            "Mirrored AllowedRemote must be exactly one dotted-decimal IPv4 address",
            "New-NetFirewallHyperVRule @HvBlockFirewallParams",
            "New-NetFirewallHyperVRule @HvFirewallParams",
            "#### 保護設定の確認後にWSL側serverを起動",
            "python3 -m http.server --bind 0.0.0.0 8080",
            "#### cleanup: server停止を保護設定の削除より先に行う",
            "Port 8080 listener remains; keep Firewall protection and stop the server first",
            "##### NAT方式のcleanup",
            "$RemainingPortProxyRows = netsh interface portproxy show v4tov4",
            "Portproxy entry remains; Firewall rules were retained",
            "##### mirrored modeのcleanup",
            "Remove-NetFirewallHyperVRule -Name $HvRuleName, $HvBlockRuleName -ErrorAction Stop",
            "#### Network Exposure Source Notes（確認日: 2026-07-20）",
        ],
        "chapter 4 exposure decision flow",
    )

    nat_section = section_between(
        chapter4,
        "#### NAT方式: portproxyとWindows Firewallを対で管理",
        "#### mirrored mode: Hyper-V Firewall ruleを個別管理",
        "chapter 4 NAT explicit deny contract",
    )
    for token in [
        '$BlockRuleName = "WSL2-Lab-NAT-TCP-8080-Block-Others"',
        "NAT AllowedRemote must be one RFC1918 LAN client",
        "$AllowedNumber = ConvertTo-IPv4UInt32 $NatAllowedRemoteAddress",
        '"0.0.0.0-$(ConvertFrom-IPv4UInt32 ([uint32]($AllowedNumber - 1)))"',
        '"$(ConvertFrom-IPv4UInt32 ([uint32]($AllowedNumber + 1)))-255.255.255.255"',
        "$BlockFirewallParams = @{",
        "Name = $BlockRuleName",
        'Action = "Block"',
        "LocalAddress = $ListenAddress",
        "LocalPort = $ListenPort",
        "RemoteAddress = $BlockedRemote",
        'Profile = "Private"',
        "New-NetFirewallRule @BlockFirewallParams -ErrorAction Stop",
        "Remove-NetFirewallRule -Name $RuleName, $BlockRuleName -ErrorAction Stop",
        "明示的なblockが競合するallowより優先",
    ]:
        require(nat_section, token, "chapter 4 NAT explicit deny contract")

    mirrored_section = section_between(
        chapter4,
        "#### mirrored mode: Hyper-V Firewall ruleを個別管理",
        "#### 保護設定の確認後にWSL側serverを起動",
        "chapter 4 mirrored explicit deny contract",
    )
    for token in [
        '$HvBlockRuleName = "WSL2-Lab-Mirrored-TCP-8080-Block-Others"',
        "Mirrored AllowedRemote must be one RFC1918 LAN client",
        "$AllowedNumber = ConvertTo-IPv4UInt32 $HvAllowedRemoteAddress",
        '"0.0.0.0-$(ConvertFrom-IPv4UInt32 ([uint32]($AllowedNumber - 1)))"',
        '"$(ConvertFrom-IPv4UInt32 ([uint32]($AllowedNumber + 1)))-255.255.255.255"',
        "$HvBlockFirewallParams = @{",
        "Name = $HvBlockRuleName",
        'Action = "Block"',
        "VMCreatorId = $WslVmCreatorId",
        "LocalPorts = 8080",
        "RemoteAddresses = $BlockedRemote",
        'Profiles = "Private"',
        "RulePriority = 1",
        "RulePriority = 2",
        "New-NetFirewallHyperVRule @HvBlockFirewallParams -ErrorAction Stop",
        "Remove-NetFirewallHyperVRule -Name $HvBlockRuleName -ErrorAction SilentlyContinue",
        "小さい`RulePriority`から評価",
    ]:
        require(mirrored_section, token, "chapter 4 mirrored explicit deny contract")

    for token in [
        "local確認ではportproxyやFirewall許可ruleを追加しません",
        "Firewall設定前にwildcard serverを起動してはいけません",
        "blocking baselineとscoped ruleを確認する",
        "baseline確認またはrule作成に失敗した場合はserverを起動せず",
        "Windowsの特定LAN IPv4へのportproxy",
        "portproxyは作成しない",
        'if ($ListenAddress -eq "0.0.0.0") { throw "Use one Windows LAN IPv4" }',
        "[System.Net.IPAddress]::TryParse($AllowedRemote, [ref]$NatAllowedRemoteAddress)",
        "$NatAllowedRemoteAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork",
        "$NatAllowedRemoteAddress.ToString() -cne $AllowedRemote",
        "NAT AllowedRemote must be one RFC1918 LAN client",
        '"0.0.0.0-$(ConvertFrom-IPv4UInt32 ([uint32]($AllowedNumber - 1)))"',
        '"$(ConvertFrom-IPv4UInt32 ([uint32]($AllowedNumber + 1)))-255.255.255.255"',
        "Get-NetConnectionProfile -InterfaceIndex $ListenInterface.InterfaceIndex -ErrorAction Stop",
        'if ($ListenProfile.NetworkCategory -ne "Private") { throw "The listen interface must use the Private profile" }',
        "Get-NetFirewallProfile -PolicyStore ActiveStore -Name Private -ErrorAction Stop",
        'if ($PrivateFirewallProfile.Enabled.ToString() -cne "True") { throw "Windows Private Firewall must be enabled" }',
        'if ($PrivateFirewallProfile.DefaultInboundAction.ToString() -cne "Block") { throw "Windows Private Firewall default inbound action must be Block" }',
        'if ($PrivateFirewallProfile.AllowLocalFirewallRules.ToString() -cne "True") { throw "Windows Private Firewall must allow local rules" }',
        'Get-NetFirewallRule -Name $RuleName -ErrorAction SilentlyContinue) { throw "Allow RuleName already exists"',
        'Get-NetFirewallRule -Name $BlockRuleName -ErrorAction SilentlyContinue) { throw "Block RuleName already exists"',
        '$ExistingProxy = $PortProxyRows | Select-String -Pattern "^\\s*$([regex]::Escape($ListenAddress))\\s+$ListenPort\\s+"',
        "Name = $RuleName",
        "Name = $BlockRuleName",
        'Action = "Block"',
        "LocalAddress = $ListenAddress",
        "LocalPort = $ListenPort",
        "RemoteAddress = $AllowedRemote",
        "RemoteAddress = $BlockedRemote",
        'Profile = "Private"',
        "Get-NetFirewallAddressFilter",
        "Portproxy add failed and cleanup state cannot be inspected; Firewall rules were retained",
        "Portproxy add and rollback failed; Firewall rules were retained",
        "Portproxy rollback could not be verified; Firewall rules were retained",
        "no proxy remains and both Firewall rules were rolled back",
        'if ($LASTEXITCODE -ne 0) { throw "Failed to remove the portproxy entry; Firewall rules were retained" }',
        "$RemainingPortProxyRows = netsh interface portproxy show v4tov4",
        "$RemainingProxy = $RemainingPortProxyRows | Select-String",
        'if ($RemainingProxy) { throw "Portproxy entry remains; Firewall rules were retained" }',
        "netsh interface portproxy delete v4tov4 listenport=$ListenPort listenaddress=$ListenAddress\n"
        'if ($LASTEXITCODE -ne 0) { throw "Failed to remove the portproxy entry; Firewall rules were retained" }',
        'if ($RemainingProxy) { throw "Portproxy entry remains; Firewall rules were retained" }\n\n'
        "Remove-NetFirewallRule -Name $RuleName, $BlockRuleName -ErrorAction Stop",
        "Get-NetFirewallRule -Name $RuleName, $BlockRuleName -ErrorAction SilentlyContinue",
        "削除後の`TcpTestSucceeded`は`False`",
        "Port 8080 listener remains; keep Firewall protection and stop the server first",
        "待受が残る場合はFirewall保護を削除しません",
        "mirrored modeでは`Test-NetConnection -ComputerName <WSL-LAN-IPv4> -Port 8080`",
        "ip -4 addr show scope global",
        '$WslVmCreatorId = "{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}"',
        "[System.Net.IPAddress]::TryParse($AllowedRemote, [ref]$HvAllowedRemoteAddress)",
        "$HvAllowedRemoteAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork",
        "$HvAllowedRemoteAddress.ToString() -cne $AllowedRemote",
        "Mirrored AllowedRemote must be one RFC1918 LAN client",
        "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -VMCreatorId $WslVmCreatorId",
        "Get-NetFirewallHyperVProfile -PolicyStore ActiveStore -Name $WslVmCreatorId -Profile Private -ErrorAction Stop",
        'if ($HvPrivateProfile.Enabled.ToString() -cne "True") { throw "Hyper-V Private Firewall must be enabled" }',
        'if ($HvPrivateProfile.DefaultInboundAction.ToString() -cne "Block") { throw "Hyper-V Private Firewall default inbound action must be Block" }',
        'if ($HvPrivateProfile.AllowLocalFirewallRules.ToString() -cne "True") { throw "Hyper-V Private Firewall must allow local rules" }',
        'Get-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction SilentlyContinue) { throw "Allow RuleName already exists"',
        'Get-NetFirewallHyperVRule -Name $HvBlockRuleName -ErrorAction SilentlyContinue) { throw "Block RuleName already exists"',
        "Name = $HvRuleName",
        "Name = $HvBlockRuleName",
        "VMCreatorId = $WslVmCreatorId",
        "LocalPorts = 8080",
        "RemoteAddresses = $AllowedRemote",
        "RemoteAddresses = $BlockedRemote",
        'Profiles = "Private"',
        "RulePriority = 1",
        "RulePriority = 2",
        "Get-NetFirewallHyperVRule -PolicyStore ActiveStore -Name $HvRuleName, $HvBlockRuleName",
        "Get-NetFirewallHyperVRule -Name $HvRuleName, $HvBlockRuleName -ErrorAction SilentlyContinue",
        "引数なしの`Remove-NetFirewallHyperVRule`は全ruleを削除し得る",
        "組織ポリシー",
        "https://learn.microsoft.com/en-us/windows/wsl/networking",
        "windows-firewall/rules",
        "windows-firewall/hyper-v-firewall",
        "wfascimprov/msft-netfirewallhypervrule",
        "powershell/module/netsecurity/new-netfirewallrule",
        "powershell/module/netsecurity/remove-netfirewallrule",
        "powershell/module/netsecurity/get-netfirewallprofile",
        "powershell/module/netsecurity/new-netfirewallhypervrule",
        "powershell/module/netsecurity/remove-netfirewallhypervrule",
        "powershell/module/netsecurity/get-netfirewallhypervvmsetting",
        "powershell/module/netsecurity/get-netfirewallhypervprofile",
        "https://nginx.org/en/docs/http/ngx_http_core_module.html#listen",
        "https://docs.python.org/3/library/http.server.html#cmdoption-http-server-bind",
        "https://nodejs.org/api/net.html#serverlisten",
        "Node.js 20 は 2026-04-30 に EOL",
        "https://github.com/nodejs/release#release-schedule",
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
        r"Node\.js 20 は 2026-03-24 に EOL",
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
        "Firewall設定前にwildcard serverを起動してはいけません",
        "ip -4 addr show scope global",
        "WSL2-Lab-NAT-TCP-8080",
        "WSL2-Lab-NAT-TCP-8080-Block-Others",
        "The listen address and port already have a portproxy entry",
        "Portproxy rollback could not be verified; Firewall rules were retained",
        "NAT AllowedRemote must be exactly one dotted-decimal IPv4 address",
        "NAT AllowedRemote must be one RFC1918 LAN client",
        "Windows Private Firewall default inbound action must be Block",
        "Windows Private Firewall must allow local rules",
        "RemoteAddress = $AllowedRemote",
        'Profile = "Private"',
        "Remove-NetFirewallRule -Name $RuleName, $BlockRuleName -ErrorAction Stop",
        "netsh interface portproxy delete v4tov4",
        "Portproxy entry remains; Firewall rules were retained",
        "Port 8080 listener remains; keep Firewall protection and stop the server first",
        "WSL2-Lab-Mirrored-TCP-8080",
        "WSL2-Lab-Mirrored-TCP-8080-Block-Others",
        "Mirrored AllowedRemote must be exactly one dotted-decimal IPv4 address",
        "Mirrored AllowedRemote must be one RFC1918 LAN client",
        "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -VMCreatorId $WslVmCreatorId",
        "Hyper-V Private Firewall default inbound action must be Block",
        "Hyper-V Private Firewall must allow local rules",
        "RemoteAddresses = $AllowedRemote",
        'Profiles = "Private"',
        "RulePriority = 1",
        "RulePriority = 2",
        "Remove-NetFirewallHyperVRule -Name $HvRuleName, $HvBlockRuleName -ErrorAction Stop",
        "Network Exposure Source Notes（確認日: 2026-07-20）",
        "Node.js 20 は 2026-04-30 に EOL",
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
        r"Node\.js 20 は 2026-03-24 に EOL",
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
            "dangling policy symlink accepted",
            "chapter3",
            "if [ -e /usr/sbin/policy-rc.d ] || [ -L /usr/sbin/policy-rc.d ]; then",
            "if [ -e /usr/sbin/policy-rc.d ]; then",
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
            "unguarded temporary policy write",
            "chapter3",
            "if ! printf '%s\\n' '#!/bin/sh' 'exit 101' | sudo tee /usr/sbin/policy-rc.d >/dev/null; then",
            "printf '%s\\n' '#!/bin/sh' 'exit 101' | sudo tee /usr/sbin/policy-rc.d >/dev/null",
            "local Nginx",
        ),
        (
            "unguarded temporary policy mode",
            "chapter3",
            "if ! sudo chmod 0755 /usr/sbin/policy-rc.d; then",
            "sudo chmod 0755 /usr/sbin/policy-rc.d",
            "install and enabled-site flow",
        ),
        (
            "missing active-service reload",
            "chapter3",
            "    if ! sudo systemctl reload nginx; then",
            "    # active process keeps its old configuration",
            "install and enabled-site flow",
        ),
        (
            "unguarded Nginx start",
            "chapter3",
            "if ! sudo systemctl start nginx; then",
            "sudo systemctl start nginx",
            "install and enabled-site flow",
        ),
        (
            "unguarded default site removal",
            "chapter3",
            "if ! sudo rm -f /etc/nginx/sites-enabled/default; then",
            "sudo rm -f /etc/nginx/sites-enabled/default",
            "install and enabled-site flow",
        ),
        (
            "missing listener fail-closed stop",
            "chapter3",
            'echo "Unexpected non-loopback Nginx listener remains" >&2\n    stop_nginx_fail_closed\n    exit 1',
            'echo "Unexpected non-loopback Nginx listener remains" >&2\n    exit 1',
            "local Nginx",
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
        ("broad Windows profile", "chapter4", 'Profile = "Private"', 'Profile = "Any"', "unsafe network guidance"),
        (
            "wildcard server before protection",
            "chapter4",
            "#### NAT方式: portproxyとWindows Firewallを対で管理",
            "python3 -m http.server --bind 0.0.0.0 8080\n\n"
            "#### NAT方式: portproxyとWindows Firewallを対で管理",
            "decision flow",
        ),
        (
            "missing stop-before-cleanup gate",
            "chapter4",
            "Port 8080 listener remains; keep Firewall protection and stop the server first",
            "# protection removed while server may still run",
            "decision flow",
        ),
        (
            "stale Node.js 20 EOL date",
            "chapter4",
            "Node.js 20 は 2026-04-30 に EOL",
            "Node.js 20 は 2026-03-24 に EOL",
            "protected exposure",
        ),
        (
            "missing Windows blocking baseline",
            "chapter4",
            "Windows Private Firewall default inbound action must be Block",
            "# Windows inbound baseline not checked",
            "protected exposure",
        ),
        (
            "missing Hyper-V blocking baseline",
            "chapter4",
            "Hyper-V Private Firewall default inbound action must be Block",
            "# Hyper-V inbound baseline not checked",
            "protected exposure",
        ),
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
            "Portproxy rollback could not be verified; Firewall rules were retained",
            "# failed native command ignored",
            "decision flow",
        ),
        (
            "missing NAT explicit block",
            "chapter4",
            "New-NetFirewallRule @BlockFirewallParams -ErrorAction Stop",
            "# explicit block omitted",
            "decision flow",
        ),
        (
            "missing NAT RFC1918 validation",
            "chapter4",
            "NAT AllowedRemote must be one RFC1918 LAN client",
            "# non-LAN remote accepted",
            "NAT explicit deny contract",
        ),
        (
            "missing NAT deny action",
            "chapter4",
            '    Action = "Block"\n    Protocol = "TCP"\n    LocalAddress = $ListenAddress',
            '    Action = "Allow"\n    Protocol = "TCP"\n    LocalAddress = $ListenAddress',
            "NAT explicit deny contract",
        ),
        (
            "missing NAT complement range",
            "chapter4",
            '"0.0.0.0-$(ConvertFrom-IPv4UInt32 ([uint32]($AllowedNumber - 1)))"',
            '"0.0.0.0-$AllowedRemote"',
            "NAT explicit deny contract",
        ),
        (
            "missing Windows rule cleanup",
            "chapter4",
            'if ($RemainingProxy) { throw "Portproxy entry remains; Firewall rules were retained" }\n\n'
            "Remove-NetFirewallRule -Name $RuleName, $BlockRuleName -ErrorAction Stop",
            'if ($RemainingProxy) { throw "Portproxy entry remains; Firewall rules were retained" }\n\n'
            "Disable-NetFirewallRule -Name $RuleName",
            "protected exposure",
        ),
        (
            "missing portproxy cleanup",
            "chapter4",
            "netsh interface portproxy delete v4tov4 listenport=$ListenPort listenaddress=$ListenAddress\n"
            'if ($LASTEXITCODE -ne 0) { throw "Failed to remove the portproxy entry; Firewall rules were retained" }',
            "netsh interface portproxy show v4tov4\n"
            '# deletion failure ignored',
            "protected exposure",
        ),
        (
            "firewall removed before proxy absence verification",
            "chapter4",
            'if ($RemainingProxy) { throw "Portproxy entry remains; Firewall rules were retained" }\n\n'
            "Remove-NetFirewallRule -Name $RuleName, $BlockRuleName -ErrorAction Stop",
            "Remove-NetFirewallRule -Name $RuleName, $BlockRuleName -ErrorAction Stop\n"
            'if ($RemainingProxy) { throw "Portproxy entry remains; Firewall rules were retained" }',
            "protected exposure",
        ),
        (
            "wildcard Windows listen",
            "chapter4",
            "$ListenAddress = Read-Host \"Windows LAN IPv4 (not 0.0.0.0)\"",
            '$ListenAddress = "0.0.0.0"',
            "unsafe network guidance",
        ),
        (
            "missing Hyper-V explicit block",
            "chapter4",
            "New-NetFirewallHyperVRule @HvBlockFirewallParams -ErrorAction Stop",
            "# Hyper-V explicit block omitted",
            "decision flow",
        ),
        (
            "missing Hyper-V block priority",
            "chapter4",
            "RulePriority = 1",
            "RulePriority = 3",
            "mirrored explicit deny contract",
        ),
        (
            "missing Hyper-V deny action",
            "chapter4",
            '    Action = "Block"\n    VMCreatorId = $WslVmCreatorId',
            '    Action = "Allow"\n    VMCreatorId = $WslVmCreatorId',
            "mirrored explicit deny contract",
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
            "unsafe network guidance",
        ),
        (
            "missing Hyper-V cleanup",
            "chapter4",
            "Remove-NetFirewallHyperVRule -Name $HvRuleName, $HvBlockRuleName -ErrorAction Stop",
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
