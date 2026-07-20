---
title: "第4章: ネットワークの基礎"
chapter: chapter4
layout: book
---

# 第4章: ネットワークの基礎

## 前提（検証環境）
- WSL2 上の Ubuntu（例: 22.04/24.04）
- Windows 側の操作（例: `netsh interface portproxy`）は PowerShell を管理者権限で実行する
- 章内で `lsof` / `netcat-openbsd` をインストールする（`sudo` が必要）
- WSL ネットワーク仕様の確認日: 2026-07-11。既定 NAT と Windows 11 22H2 以降の mirrored mode を区別する

## この章の目標
- ネットワークの基本概念を説明できる
- WSL2 のネットワーク特性を把握する
- 基本的なネットワークコマンドを使って状態確認ができる

## できるようになること
- ネットワークの接続状態を確認できる
- Web サーバーにアクセスできる
- ネットワークトラブルを一次切り分けできる

## はじめに：ネットワークを理解する

この章では、コンピュータ同士がどうやって通信するかを学びます。
特に WSL2 環境での仕組みを理解することが重要です。

### 用語の整理（例）
- **IP アドレス**: 通信先を識別するアドレス
- **ポート番号**: サービス（プロセス）を識別する番号
- **ping**: 疎通（到達性）の確認
- **curl**: HTTP/HTTPS 等でのデータ取得

## 4.1 WSL2 のネットワーク構造

### WSL2 ネットワークの特性

WSL2 は仮想化された Linux 環境として動作します。既定は NAT 方式ですが、Windows 11 22H2 以降では mirrored mode も選択できます。まず自分の設定を確認し、ネットワーク方式を決めつけないことが重要です。

概念上は、次のように整理できます。
- **Windows**: 外部ネットワークに接続するホスト
- **WSL2**: ホスト内の仮想ネットワークに接続するゲスト
- **NAT**: アドレス変換により外部との通信を中継する仕組み

### WSL2 ネットワークアーキテクチャ

既定の NAT 方式では、WSL2 は独自の仮想ネットワークアダプタを持ち、Windows ホストとは NAT 経由で通信します。mirrored mode では Windows のネットワークインターフェースを Linux 側へ反映するため、IP アドレス、IPv6、VPN、LAN からの到達性、Firewall の扱いが NAT 方式と異なります。

![WSL2 ネットワーク構造図]({{ site.baseurl }}/assets/images/wsl2-network-structure.svg)

この図は、WSL2 が Windows ホストと連携してネットワーク通信を行う流れを示しています。

```bash
# WSL2 の IP アドレス確認（内部 IP）
ip addr show eth0
# 出力例：172.x.x.x（これは内部専用）

# NAT 方式で Windows ホストの IP を確認（WSL2 から見た default gateway）
ip route show default | awk '{print $3; exit}'
# 出力例：172.x.x.1
```

注意点は次のとおりです。
- NAT 方式では WSL2 の IP アドレスが再起動で変わる場合がある
- NAT 方式では外部ネットワークから WSL2 へ直接アクセスできず、port proxy 等が必要な場合がある
- Windows から WSL2 内の TCP サービスへは、既定設定でも通常 `localhost` でアクセスできる
- DNS tunneling が有効な環境では、`/etc/resolv.conf` の nameserver を Windows ホストの IP として流用しない

Windows 11 22H2 以降で mirrored mode を利用する場合は、Windows ユーザーのホームにある `.wslconfig` へ次を設定し、PowerShell で `wsl --shutdown` を実行します。これは全ディストリビューションを停止するため、作業を保存してから実行してください。

```ini
[wsl2]
networkingMode=mirrored
```

mirrored mode で LAN からの受信を許可する場合は、Hyper-V FirewallのActiveStoreと、そこへmergeされるWindows Firewall/GPO/CSPのpolicyを確認します。組織管理 PC ではポリシーを優先してください。

### local確認（既定・推奨）

```bash
# WSL2内のloopbackだけで一時serverを起動
python3 -m http.server --bind 127.0.0.1 8000

# 別terminalで待受addressとWSL内の疎通を確認
ss -ltnp '( sport = :8000 )'
curl --fail http://127.0.0.1:8000/
```

Windows PowerShellからも確認します。

```powershell
Test-NetConnection -ComputerName localhost -Port 8000
```

`TcpTestSucceeded`が`True`であることを確認します。local確認ではportproxyやFirewall許可ruleを追加しません。検証後はPython serverを起動したterminalで`Ctrl+C`を押して終了します。

### LAN公開runbook（必要な場合だけ）
{: #wsl-lan-publication}

LAN公開はlocal確認とは別の演習です。学習用データだけを使用し、組織管理PCではGPO/CSPと管理者の指示を優先します。公開中はWSL側serverを`0.0.0.0`へbindするため、以下のFirewall制限とcleanupを省略しないでください。

| ネットワーク方式 | LANへの経路 | 必要な保護 | cleanup |
|---|---|---|---|
| NAT | Windowsの特定LAN IPv4へのportproxy | Windows Firewallを`Private` profile、特定client IPv4、特定portへ限定 | Firewall ruleとportproxyを両方削除 |
| mirrored mode | LANからWSLへ直接接続。portproxyは作成しない | WSL用Hyper-V Firewall ruleを`Private` profile、特定client IPv4、特定portへ限定 | Hyper-V Firewall ruleを削除 |

Firewall設定前にwildcard serverを起動してはいけません。次の順序を守ります。

1. NATまたはmirrored modeの**どちらか一方**について、blocking baselineとscoped ruleを確認する
2. 保護が有効になった後で、WSL側serverを`0.0.0.0`へbindする
3. 許可clientと非許可clientから到達範囲を確認する
4. WSL側serverを停止し、待受が消えたことを確認する
5. 最後にFirewall ruleとportproxyをcleanupする

`0.0.0.0`はWSLの全IPv4 interfaceで待ち受けるため、local用serverでは使用しません。baseline確認またはrule作成に失敗した場合はserverを起動せず、設定を広げないでください。

#### NAT方式: portproxyとWindows Firewallを対で管理

管理者PowerShellで実行します。`ListenAddress`にはWindowsの対象LAN adapterに割り当てられた**特定のIPv4**、`AllowedRemote`には接続を許可する**1台の検証clientのIPv4**を入力します。`0.0.0.0`、`Any`、全profileへ広げないでください。対象adapterが`Private`でなければ実行を止め、profileを勝手に変更せず管理者へ確認します。

```powershell
$RuleName = "WSL2-Lab-NAT-TCP-8080"
$ListenPort = 8080
$Distro = Read-Host "Exact WSL distribution name"
$ListenAddress = Read-Host "Windows LAN IPv4 (not 0.0.0.0)"
$AllowedRemote = Read-Host "One allowed LAN client IPv4"
$WslAddress = (wsl.exe -d $Distro hostname -I).Trim().Split(' ')[0]

if ($ListenAddress -eq "0.0.0.0") { throw "Use one Windows LAN IPv4" }
$NatAllowedRemoteAddress = $null
if (-not [System.Net.IPAddress]::TryParse($AllowedRemote, [ref]$NatAllowedRemoteAddress) -or
    $NatAllowedRemoteAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork -or
    $NatAllowedRemoteAddress.ToString() -cne $AllowedRemote) {
    throw "NAT AllowedRemote must be exactly one dotted-decimal IPv4 address"
}
if (Get-NetFirewallRule -Name $RuleName -ErrorAction SilentlyContinue) { throw "RuleName already exists" }
$ListenInterface = Get-NetIPAddress -AddressFamily IPv4 -IPAddress $ListenAddress -ErrorAction Stop
$ListenProfile = Get-NetConnectionProfile -InterfaceIndex $ListenInterface.InterfaceIndex -ErrorAction Stop
if ($ListenProfile.NetworkCategory -ne "Private") { throw "The listen interface must use the Private profile" }
$PrivateFirewallProfile = Get-NetFirewallProfile -PolicyStore ActiveStore -Name Private -ErrorAction Stop
if ($PrivateFirewallProfile.Enabled.ToString() -cne "True") { throw "Windows Private Firewall must be enabled" }
if ($PrivateFirewallProfile.DefaultInboundAction.ToString() -cne "Block") { throw "Windows Private Firewall default inbound action must be Block" }
if ($PrivateFirewallProfile.AllowLocalFirewallRules.ToString() -cne "True") { throw "Windows Private Firewall must allow local rules" }

# 既存proxyを引き継いだり削除したりしないよう、同じlisten endpointが未使用であることを確認
$PortProxyRows = netsh interface portproxy show v4tov4
if ($LASTEXITCODE -ne 0) { throw "Failed to inspect existing portproxy entries" }
$ExistingProxy = $PortProxyRows | Select-String -Pattern "^\s*$([regex]::Escape($ListenAddress))\s+$ListenPort\s+"
if ($ExistingProxy) { throw "The listen address and port already have a portproxy entry" }

netsh interface portproxy add v4tov4 listenport=$ListenPort listenaddress=$ListenAddress connectport=8080 connectaddress=$WslAddress
if ($LASTEXITCODE -ne 0) { throw "Failed to create portproxy; Firewall rule was not created" }
$FirewallParams = @{
    Name = $RuleName
    DisplayName = "WSL2 lab TCP 8080 (Private, one client)"
    Direction = "Inbound"
    Action = "Allow"
    Protocol = "TCP"
    LocalAddress = $ListenAddress
    LocalPort = $ListenPort
    RemoteAddress = $AllowedRemote
    Profile = "Private"
}
try {
    New-NetFirewallRule @FirewallParams -ErrorAction Stop
} catch {
    # このrunbookが作成したproxyだけをrollbackする
    netsh interface portproxy delete v4tov4 listenport=$ListenPort listenaddress=$ListenAddress
    if ($LASTEXITCODE -ne 0) { Write-Error "Firewall rule creation and portproxy rollback both failed" }
    throw
}

# serverを起動する前に保護設定を確認
netsh interface portproxy show v4tov4
Get-NetFirewallRule -Name $RuleName | Format-List Name, Enabled, Profile, Direction, Action
Get-NetFirewallRule -Name $RuleName | Get-NetFirewallAddressFilter | Format-List LocalAddress, RemoteAddress
```

作成からcleanupまでは変数を保持した同じ管理者PowerShellを使用します。作成途中または確認が失敗した場合はserverを起動せず、ruleを広げないでください。

#### mirrored mode: Hyper-V Firewall ruleを個別管理

mirrored modeではportproxyと上のWindows Firewall ruleを作成しません。Windows 11 22H2以降のHyper-V Firewall設定とactive profileを確認し、WSLのVMCreatorIdに個別ruleを作成します。組織ポリシーでlocal ruleが許可されない場合やblocking baselineを確認できない場合は、`Any`へ広げず管理者へ確認します。

```powershell
$HvRuleName = "WSL2-Lab-Mirrored-TCP-8080"
$WslVmCreatorId = "{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}"
$AllowedRemote = Read-Host "One allowed LAN client IPv4"

$HvAllowedRemoteAddress = $null
if (-not [System.Net.IPAddress]::TryParse($AllowedRemote, [ref]$HvAllowedRemoteAddress) -or
    $HvAllowedRemoteAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork -or
    $HvAllowedRemoteAddress.ToString() -cne $AllowedRemote) {
    throw "Mirrored AllowedRemote must be exactly one dotted-decimal IPv4 address"
}
Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -VMCreatorId $WslVmCreatorId
$HvPrivateProfile = Get-NetFirewallHyperVProfile -PolicyStore ActiveStore -Name $WslVmCreatorId -Profile Private -ErrorAction Stop
if ($HvPrivateProfile.Enabled.ToString() -cne "True") { throw "Hyper-V Private Firewall must be enabled" }
if ($HvPrivateProfile.DefaultInboundAction.ToString() -cne "Block") { throw "Hyper-V Private Firewall default inbound action must be Block" }
if ($HvPrivateProfile.AllowLocalFirewallRules.ToString() -cne "True") { throw "Hyper-V Private Firewall must allow local rules" }
if (Get-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction SilentlyContinue) { throw "RuleName already exists" }
$HvFirewallParams = @{
    Name = $HvRuleName
    DisplayName = "WSL2 lab mirrored TCP 8080 (Private, one client)"
    Direction = "Inbound"
    Action = "Allow"
    VMCreatorId = $WslVmCreatorId
    Protocol = "TCP"
    LocalPorts = 8080
    RemoteAddresses = $AllowedRemote
    Profiles = "Private"
}
New-NetFirewallHyperVRule @HvFirewallParams -ErrorAction Stop

# serverを起動する前に保護設定を確認
Get-NetFirewallHyperVRule -PolicyStore ActiveStore -Name $HvRuleName | Format-List Name, Enabled, Direction, Profiles, RemoteAddresses, LocalPorts
```

作成からcleanupまでは変数を保持した同じ管理者PowerShellを使用します。Hyper-V ruleの作成または確認に失敗した場合はserverを起動しません。

#### 保護設定の確認後にWSL側serverを起動

上のどちらか一方の保護設定が成功した後だけ、WSL側でLAN演習専用serverを起動します。

```bash
python3 -m http.server --bind 0.0.0.0 8080

# 別terminalで0.0.0.0:8080の待受とlocal応答を確認
ss -ltnp '( sport = :8080 )'
ip -4 addr show scope global
curl --fail http://127.0.0.1:8080/
```

許可したLAN clientから、NAT方式では`Test-NetConnection -ComputerName <Windows-LAN-IPv4> -Port 8080`、mirrored modeでは`Test-NetConnection -ComputerName <WSL-LAN-IPv4> -Port 8080`を実行し`True`を確認します。mirrored modeの宛先は上の`ip -4 addr show scope global`で確認したWSLのLAN IPv4です。許可していない別clientからは同じ宛先への結果が`False`であることを確認します。期待値と異なる場合はruleを広げず、次の順序でcleanupします。

#### cleanup: server停止を保護設定の削除より先に行う

最初にPython serverを起動したWSL terminalで`Ctrl+C`を押します。別のWSL terminalで待受が消えたことを確認します。

```bash
if ss -H -ltn '( sport = :8080 )' | grep -q .; then
    echo "Port 8080 listener remains; keep Firewall protection and stop the server first" >&2
    exit 1
fi
```

待受が残る場合はFirewall保護を削除しません。server停止を確認できた場合だけ、設定した方式のcleanupへ進みます。

##### NAT方式のcleanup

変数を保持した同じ管理者PowerShellで、受信許可とportproxyを個別に削除します。

```powershell
Remove-NetFirewallRule -Name $RuleName -ErrorAction Stop
netsh interface portproxy delete v4tov4 listenport=$ListenPort listenaddress=$ListenAddress
if ($LASTEXITCODE -ne 0) { throw "Failed to remove the portproxy entry" }

if (Get-NetFirewallRule -Name $RuleName -ErrorAction SilentlyContinue) { throw "Firewall rule remains" }
netsh interface portproxy show v4tov4
Test-NetConnection -ComputerName $ListenAddress -Port $ListenPort
```

削除後の`TcpTestSucceeded`は`False`、`netsh`の一覧には同じaddress/portの行がないことが期待値です。

##### mirrored modeのcleanup

**必ず一意なNameを指定して**削除します。引数なしの`Remove-NetFirewallHyperVRule`は全ruleを削除し得るため、本書では使用しません。

```powershell
Remove-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction Stop
if (Get-NetFirewallHyperVRule -Name $HvRuleName -ErrorAction SilentlyContinue) { throw "Hyper-V Firewall rule remains" }
```

許可していたLAN clientから再度`Test-NetConnection`を実行し、`TcpTestSucceeded`が`False`であることを確認します。process停止とrule削除の両方を確認してcleanup完了とします。

#### Network Exposure Source Notes（確認日: 2026-07-20）

- [Accessing network applications with WSL](https://learn.microsoft.com/en-us/windows/wsl/networking): NATのlocalhost forwarding、portproxyの`listenaddress`、mirrored mode、Hyper-V Firewallの適用境界を確認しました。
- [Configure Hyper-V firewall](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/hyper-v-firewall): WSL VMCreatorId、ActiveStore、profile、個別ruleの確認方法を確認しました。
- [Get-NetFirewallHyperVVMSetting](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallhypervvmsetting): VM設定の`Name` parameterに`VMCreatorId` aliasがあり、VM creator IDを明示して取得できることを確認しました。
- [New-NetFirewallRule](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule) / [Remove-NetFirewallRule](https://learn.microsoft.com/en-us/powershell/module/netsecurity/remove-netfirewallrule): 一意なName、address/profile条件、個別rule削除を確認しました。
- [Get-NetFirewallProfile](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallprofile): Windows FirewallのActiveStoreにおける有効状態、既定inbound action、local rule mergeを確認しました。
- [New-NetFirewallHyperVRule](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallhypervrule) / [Remove-NetFirewallHyperVRule](https://learn.microsoft.com/en-us/powershell/module/netsecurity/remove-netfirewallhypervrule): `RemoteAddresses`、`Profiles`、一意なNameによる作成・削除を確認しました。
- [Get-NetFirewallHyperVProfile](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallhypervprofile): WSL VMCreatorIdのPrivate profileについて、ActiveStoreの有効状態、既定inbound action、local rule mergeを確認しました。
- [NGINX `listen` directive](https://nginx.org/en/docs/http/ngx_http_core_module.html#listen): addressを指定したsocketの待受範囲を確認しました。
- [Python `http.server --bind`](https://docs.python.org/3/library/http.server.html#cmdoption-http-server-bind): command lineで待受addressを明示する方法を確認しました。
- [Node.js `net.Server.listen`](https://nodejs.org/api/net.html#serverlisten): host省略時はIPv6 `::`またはIPv4 `0.0.0.0`で待ち受けるため、local例ではhostを省略しません。
- [Node.js release schedule](https://github.com/nodejs/release#release-schedule): Node.js 20のEOLが2026-04-30であることを確認しました。

### ネットワーク設定ファイル

```bash
# DNS 設定
cat /etc/resolv.conf

# ホスト名解決
cat /etc/hosts

# ネットワークインターフェース設定
cat /etc/netplan/*.yaml  # Ubuntu（netplan採用）
# WSL2 では自動生成のため編集不要
```

## 4.2 基本ネットワークコマンド

### ip - ネットワーク設定表示

```bash
# インターフェース一覧
ip link show

# IP アドレス表示
ip addr show
ip a  # 省略形

# ルーティングテーブル
ip route show
ip r  # 省略形

# 特定インターフェースの詳細
ip addr show eth0
```

### ping - 疎通確認

```bash
# 基本的な疎通確認
ping google.com

# 回数指定
ping -c 4 google.com

# パケットサイズ指定
ping -s 1000 google.com

# 連続ping（1秒間隔）
ping -i 1 192.168.1.1

# タイムアウト設定
ping -W 2 -c 3 unreachable.host
```

pingの結果解釈は次のとおりです。
```text
64 bytes from 142.250.x.x: icmp_seq=1 ttl=115 time=8.45 ms
│                │              │       │        └─ 応答時間
│                │              │       └─ TTL（Time To Live）
│                │              └─ シーケンス番号
│                └─ 応答元 IP
└─ パケットサイズ
```

### traceroute - 経路追跡

```bash
# インストール
sudo apt install -y traceroute

# 経路追跡
traceroute google.com

# UDPの代わりにICMP使用
traceroute -I google.com

# 最大ホップ数指定
traceroute -m 10 google.com
```

### nslookup/dig - DNS 問い合わせ

```bash
# nslookup基本
nslookup google.com

# 特定 DNS サーバー指定
nslookup google.com 8.8.8.8

# dig（より詳細）
sudo apt install -y dnsutils
dig google.com

# 特定レコードタイプ
dig google.com MX  # メールサーバー
dig google.com TXT # テキストレコード
dig google.com A   # IPv4アドレス
dig google.com AAAA # IPv6アドレス

# 簡潔な出力
dig +short google.com
```

## 4.3 ポートとサービス

### ss/netstat - ポート確認

```bash
# ssコマンド（推奨）
# リスニングポート表示
ss -tln  # TCPのみ
ss -uln  # UDPのみ
ss -tlnp # プロセス情報付き（要sudo）

# 全接続表示
ss -tan  # TCP接続
ss -uan  # UDP接続

# 特定ポート検索
ss -tan | grep :80
```

出力の読み方は次のとおりです。
```text
State  Recv-Q Send-Q Local Address:Port   Peer Address:Port Process
LISTEN 0      511    127.0.0.1:80         0.0.0.0:*     nginx
│      │      │      │                    │             └─ プロセス名
│      │      │      │                    └─ 接続先（*は任意）
│      │      │      └─ ローカルアドレス:ポート
│      │      └─ 送信キュー
│      └─ 受信キュー
└─ 状態
```

### lsof - ポート使用プロセス特定

```bash
# インストール
sudo apt install -y lsof

# 特定ポート使用プロセス
sudo lsof -i :80
sudo lsof -i :8080

# TCP接続のみ
sudo lsof -i TCP

# 特定プロセスのネットワーク接続
sudo lsof -i -p PID
```

### curl - HTTP クライアント

```bash
# 基本的なGET
curl http://example.com

# ヘッダーのみ取得
curl -I http://example.com

# 詳細表示
curl -v http://example.com

# POSTリクエスト
curl -X POST -d "name=value" http://example.com/api

# JSON データ送信
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}' \
  http://api.example.com/endpoint

# ファイルダウンロード
curl -O http://example.com/file.zip  # 元のファイル名
curl -o myfile.zip http://example.com/file.zip  # 名前指定

# 進捗表示付きダウンロード
curl -# -O http://example.com/largefile.zip

# Basic認証（パスワードはプロンプトで入力し、履歴や引数へ残さない）
curl -u username https://example.com

# HTTP ステータスコードのみ
curl -s -o /dev/null -w "%{http_code}" http://example.com
```

### wget - ファイルダウンロード

```bash
# 基本ダウンロード
wget http://example.com/file.zip

# 再帰的ダウンロード
wget -r -l 2 http://example.com

# 再試行設定
wget --tries=3 --timeout=30 http://example.com/file.zip

# バックグラウンドダウンロード
wget -b http://example.com/largefile.zip
tail -f wget-log  # ログ確認
```

## 4.4 実践: ローカルWeb サーバー構築

### Python簡易 HTTP サーバー

```bash
# Python3 HTTP サーバー（local開発用）
cd ~/public_html
python3 -m http.server --bind 127.0.0.1 8000

# 待受addressを確認
ss -ltnp '( sport = :8000 )'

# CGI有効化時もloopbackへ限定
python3 -m http.server --bind 127.0.0.1 --cgi 8000
```

### Node.js HTTP サーバー（オプション）

この例はサポート中の Node.js 24 LTS を前提とします。Node.js 20 は 2026-04-30 に EOL となりました。未導入または EOL 版の場合は、Node.js 公式のインストール案内から環境に合う方法を選び、署名・配布元を確認してください。

```bash
# サポート中の版であることを確認
node --version
# 出力例: v24.x

# 簡易サーバー作成
cat << 'JS' > server.js
const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    
    if (req.url === '/') {
        res.writeHead(200, {'Content-Type': 'text/html'});
        res.end('<h1>Hello from Node.js on WSL2!</h1>');
    } else if (req.url === '/api/time') {
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify({time: new Date().toISOString()}));
    } else {
        res.writeHead(404);
        res.end('Not Found');
    }
});

server.listen(3000, '127.0.0.1', () => {
    console.log('Server running at http://localhost:3000/');
});
JS

# サーバー起動
node server.js

# 別ターミナルでテスト
ss -ltnp '( sport = :3000 )'
curl http://localhost:3000/
curl http://localhost:3000/api/time
```

### Netcat - 汎用ネットワークツール

```bash
# インストール
sudo apt install -y netcat-openbsd

# TCPサーバー起動（localだけで待受）
nc -l 127.0.0.1 12345

# TCPクライアント接続
nc localhost 12345

# ポートスキャン
nc -zv localhost 20-100

# ファイル転送
# 受信側：
nc -l 127.0.0.1 12345 > received_file.txt
# 送信側：
nc localhost 12345 < send_file.txt

# 簡易localチャットサーバー
# サーバー側：
nc -l 127.0.0.1 12345
# クライアント側：
nc 127.0.0.1 12345
```

※ Ubuntu では `nc` は `netcat-openbsd` が標準になりやすく、実装差により `nc -l -p ...` が動かない場合があります。本書のlocal例ではUbuntu標準環境で動く`nc -l <ADDRESS> <PORT>`を採用します。LAN公開はNetcat例を流用せず、[LAN公開runbook](#wsl-lan-publication)で範囲とcleanupを管理します。

## 4.5 ファイアウォール基礎

### ufw - 簡易ファイアウォール

```bash
# インストールと有効化
sudo apt install -y ufw

# 状態確認
sudo ufw status

# 基本ポリシー設定
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 特定ポート許可
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 特定 IP からのみ許可
sudo ufw allow from 192.168.1.100 to any port 22

# ルール削除
sudo ufw delete allow 80/tcp

# 有効化（WSL2 では通常不要）
sudo ufw enable
```

### iptables - 詳細設定

```bash
# 現在のルール表示
sudo iptables -L -n -v

# 特定ポートを開く
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# 特定 IP からの接続を拒否
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# ルール保存（再起動後も維持）
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

## 4.6 ネットワークトラブルシューティング

### 接続診断フロー

```bash
#!/bin/bash
# network_check.sh - ネットワーク診断スクリプト

echo "=== Network Diagnostics ==="

# 1. インターフェース確認
echo "1. Network Interfaces:"
ip link show | grep -E "^[0-9]:" | awk '{print $2}'

# 2. IP アドレス確認
echo -e "\n2. IP Addresses:"
ip -4 addr show | grep inet | grep -v 127.0.0.1

# 3. デフォルトゲートウェイ確認
echo -e "\n3. Default Gateway:"
ip route | grep default

# 4. DNS 確認
echo -e "\n4. DNS Servers:"
cat /etc/resolv.conf | grep nameserver

# 5. 外部接続テスト
echo -e "\n5. Connectivity Tests:"
ping -c 1 127.0.0.1 > /dev/null 2>&1 && echo "✓ Loopback" || echo "✗ Loopback"
ping -c 1 $(ip route | grep default | awk '{print $3}') > /dev/null 2>&1 && echo "✓ Gateway" || echo "✗ Gateway"
ping -c 1 8.8.8.8 > /dev/null 2>&1 && echo "✓ Internet (IP)" || echo "✗ Internet (IP)"
ping -c 1 google.com > /dev/null 2>&1 && echo "✓ DNS Resolution" || echo "✗ DNS Resolution"
```

### よくある問題と対処

| 問題 | 症状 | 対処法 |
|------|------|--------|
| localhostに接続できない | `curl: (7) Failed to connect` | サービス起動確認、ポート確認 |
| 外部から接続できない | タイムアウト | Windows Firewall 確認 |
| DNS 解決失敗 | `cannot resolve host` | `/etc/resolv.conf`確認 |
| ポート既に使用中 | `Address already in use` | `lsof -i :PORT`で確認 |
| WSL2 IP 変更 | 接続先不明 | `hostname -I`で再確認 |

### WSL2 特有の問題対処

```bash
# WSL2 の IP 自動取得スクリプト
cat << 'SCRIPT' > ~/get_wsl_ip.sh
#!/bin/bash
# WSL2 IP 取得
WSL_IP=$(hostname -I | awk '{print $1}')
WIN_IP=$(ip route show default | awk '{print $3; exit}')

echo "WSL2 IP: $WSL_IP"
echo "Windows IP (NAT mode, from WSL2): ${WIN_IP:-not detected}"

# Windows のhostsファイル更新用
echo "Add to C:\\Windows\\System32\\drivers\\etc\\hosts:"
echo "$WSL_IP wsl.local"
SCRIPT

chmod +x ~/get_wsl_ip.sh
```

この取得方法は NAT 方式向けです。mirrored mode では Windows 上のサービスへ `127.0.0.1` で接続でき、NAT 方式のホスト IP 取得が不要な場合があります。Firewallを一時変更する場合は、上の[LAN公開runbook](#wsl-lan-publication)に従って一意なrule name、送信元、profile、cleanupを対にしてください。

## 4.7 演習問題

### 演習1: ポート監視スクリプト

```bash
#!/bin/bash
# port_monitor.sh - 指定ポートの監視

PORTS="22 80 443 3306 5432"
LOG_DIR="$HOME/logs"
LOG_FILE="$LOG_DIR/port_monitor.log"

mkdir -p "$LOG_DIR"

echo "=== Port Monitoring Report ===" | tee -a "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"

for port in $PORTS; do
    if ss -tln | grep -q ":$port "; then
        service=$(ss -tlnp 2>/dev/null | grep ":$port " | awk '{print $NF}' | cut -d'"' -f2)
        echo "✓ Port $port is open (Service: ${service:-unknown})" | tee -a "$LOG_FILE"
    else
        echo "✗ Port $port is closed" | tee -a "$LOG_FILE"
    fi
done
```

### 演習2: 簡易ロードバランサー

```bash
#!/bin/bash
# simple_lb_demo.sh - バックエンド起動 + 簡易ロードバランサー

# バックエンドサーバー起動
for i in {1..3}; do
    port=$((8000 + i))
    mkdir -p ~/backend$i
    echo "<h1>Backend Server $i</h1>" > ~/backend$i/index.html
    (cd ~/backend$i && python3 -m http.server --bind 127.0.0.1 "$port") &
done

# ロードバランサー
# Ubuntu標準のncは -c をサポートしないため、Pythonで簡易ロードバランサーを実装する
cat > simple_lb.py << 'PY'
#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import itertools
import urllib.request
import urllib.error

BACKENDS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003",
]
backend_cycle = itertools.cycle(BACKENDS)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        backend = next(backend_cycle)
        url = backend + self.path
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                body = resp.read()
                status = resp.status
                content_type = resp.headers.get("Content-Type", "text/html; charset=utf-8")
        except (urllib.error.URLError, TimeoutError) as e:
            body = f"Upstream error: {e}\n".encode("utf-8")
            status = 502
            content_type = "text/plain; charset=utf-8"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("Listening on http://localhost:8000")
    server.serve_forever()
PY

python3 simple_lb.py
```

### 演習3: API 監視とアラート

```bash
#!/bin/bash
# api_health_check.sh - API 死活監視

ENDPOINTS=(
    "http://localhost:3000/health"
    "http://localhost:8080/api/status"
    "http://example.com/ping"
)

check_endpoint() {
    local url=$1
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 $url)
    
    if [ "$response" = "200" ]; then
        echo "$(date): ✓ $url is healthy (HTTP $response)"
    else
        LOG_DIR="$HOME/logs"
        LOG_FILE="$LOG_DIR/api_alerts.log"
        mkdir -p "$LOG_DIR"
        echo "$(date): ✗ $url is down (HTTP $response)" | tee -a "$LOG_FILE"
        # アラート送信（メール、Slack等）
        # echo "API Down: $url" | mail -s "API Alert" admin@example.com
    fi
}

while true; do
    for endpoint in "${ENDPOINTS[@]}"; do
        check_endpoint $endpoint
    done
    sleep 60
done
```

## 4.8 パフォーマンス測定

### 帯域幅測定

```bash
# iperfインストール
sudo apt install -y iperf3

# サーバーモード
iperf3 -s

# クライアントモード
iperf3 -c server_ip

# 詳細オプション
iperf3 -c server_ip -t 30 -P 4  # 30秒間、4並列
```

### レイテンシ測定

```bash
# mtr - 継続的なtraceroute
sudo apt install -y mtr
mtr google.com

# 統計情報のみ
mtr -r -c 100 google.com
```

### HTTP 応答時間測定

```bash
# 詳細な時間測定
curl -w @- -o /dev/null -s http://example.com << 'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
   time_pretransfer:  %{time_pretransfer}\n
      time_redirect:  %{time_redirect}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF

# 簡易ベンチマーク
for i in {1..10}; do
    time curl -s http://localhost:8000 > /dev/null
done
```

## まとめ

ネットワーク管理の要点は次のとおりです。

1. **WSL2 の特性理解**: NAT 構造とポートフォワーディング
2. **基本ツールの把握**: ping、curl、ss の日常的な利用
3. **トラブルシューティング**: 段階的な問題切り分け手法

次章では、これらの知識を活用してシェルスクリプトによる自動化を扱います。

**次章へ**: [第5章 シェルスクリプト入門](../chapter5/)
