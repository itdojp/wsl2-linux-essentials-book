---
title: "第4章: ネットワークの基礎"
chapter: chapter4
layout: book
---

# 第4章: ネットワークの基礎

## 🎯 この章の目標
- ネットワークの基本概念を理解する
- WSL2のネットワーク構造を把握する
- 基本的なネットワークコマンドを使える

## 🚀 できるようになること
- ネットワークの接続状態を確認できる
- Webサーバーにアクセスできる
- ネットワークトラブルを解決できる

## はじめに：ネットワークを理解する

この章では、コンピュータ同士がどうやって通信するかを学びます。
特にWSL2環境での特殊な仕組みを理解することが重要です。

### 🌐 身近な例で理解する
- **IPアドレス** = 住所（どこに送るか）
- **ポート番号** = 部屋番号（どのサービスに送るか）
- **ping** = 生存確認（「生きてる？」と聞く）
- **curl** = データ取得（「これください」と頼む）

## 4.1 WSL2のネットワーク構造

### WSL2ネットワークの特殊性

WSL2は「Windows の中の Linux」なので、ネットワークも特殊な構造になっています。

#### 💡 例え話：マンションの中のシェアハウス
- **Windows** = マンション全体（実際の住所を持つ）
- **WSL2** = マンション内のシェアハウス（内部番号のみ）
- **NAT** = 受付（外部との連絡を仲介）

### WSL2ネットワークアーキテクチャ

WSL2は仮想マシンとして動作し、独自の仮想ネットワークアダプタを持ちます。WindowsホストとはNAT経由で通信します。

![WSL2ネットワーク構造図]({{ site.baseurl }}/assets/images/wsl2-network-structure.svg)

この図は、WSL2がどのようにWindowsホストと連携してネットワーク通信を行うかを示しています。WSL2は専用の仮想ネットワークアダプタを通じて、NATによる変換を経てWindowsホストのネットワークにアクセスします。

```bash
# WSL2のIPアドレス確認（内部IP）
ip addr show eth0
# 出力例：172.x.x.x（これは内部専用）

# WindowsのIP確認（WSL2から見た）
cat /etc/resolv.conf | grep nameserver
# 出力例：172.x.x.1（Windowsへの経路）
```

⚠️ **重要な注意点**：
- WSL2のIPは起動のたびに変わることがある
- 外部からWSL2に直接アクセスはできない（NATの壁）
- でも心配不要！localhostで自動転送される

### ポートフォワーディングの仕組み

```bash
# WSL2 → Windows: 自動転送
# WSL2でサーバー起動
python3 -m http.server 8000

# Windowsブラウザでアクセス可能
# http://localhost:8000

# Windows → WSL2: 手動設定が必要な場合
# PowerShell（管理者）で実行
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$(wsl hostname -I)
```

### ネットワーク設定ファイル

```bash
# DNS設定
cat /etc/resolv.conf

# ホスト名解決
cat /etc/hosts

# ネットワークインターフェース設定
cat /etc/netplan/*.yaml  # Ubuntu 18.04以降
# WSL2では自動生成のため編集不要
```

## 4.2 基本ネットワークコマンド

### ip - ネットワーク設定表示

```bash
# インターフェース一覧
ip link show

# IPアドレス表示
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

pingの結果解釈：
```
64 bytes from 142.250.x.x: icmp_seq=1 ttl=115 time=8.45 ms
│                │              │       │        └─ 応答時間
│                │              │       └─ TTL（Time To Live）
│                │              └─ シーケンス番号
│                └─ 応答元IP
└─ パケットサイズ
```

### traceroute - 経路追跡

```bash
# インストール
sudo apt install traceroute -y

# 経路追跡
traceroute google.com

# UDPの代わりにICMP使用
traceroute -I google.com

# 最大ホップ数指定
traceroute -m 10 google.com
```

### nslookup/dig - DNS問い合わせ

```bash
# nslookup基本
nslookup google.com

# 特定DNSサーバー指定
nslookup google.com 8.8.8.8

# dig（より詳細）
sudo apt install dnsutils -y
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

出力の読み方：
```
State  Recv-Q Send-Q Local Address:Port   Peer Address:Port Process
LISTEN 0      511    0.0.0.0:80           0.0.0.0:*     nginx
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
sudo apt install lsof -y

# 特定ポート使用プロセス
sudo lsof -i :80
sudo lsof -i :8080

# TCP接続のみ
sudo lsof -i TCP

# 特定プロセスのネットワーク接続
sudo lsof -i -p PID
```

### curl - HTTPクライアント

```bash
# 基本的なGET
curl http://example.com

# ヘッダーのみ取得
curl -I http://example.com

# 詳細表示
curl -v http://example.com

# POSTリクエスト
curl -X POST -d "name=value" http://example.com/api

# JSONデータ送信
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}' \
  http://api.example.com/endpoint

# ファイルダウンロード
curl -O http://example.com/file.zip  # 元のファイル名
curl -o myfile.zip http://example.com/file.zip  # 名前指定

# 進捗表示付きダウンロード
curl -# -O http://example.com/largefile.zip

# Basic認証
curl -u username:password http://example.com

# HTTPステータスコードのみ
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

## 4.4 実践: ローカルWebサーバー構築

### Python簡易HTTPサーバー

```bash
# Python3 HTTPサーバー（開発用）
cd ~/public_html
python3 -m http.server 8000

# 特定IPでバインド
python3 -m http.server 8000 --bind 127.0.0.1

# CGI有効化
python3 -m http.server --cgi 8000
```

### Node.js HTTPサーバー

```bash
# Node.jsインストール
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

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

server.listen(3000, () => {
    console.log('Server running at http://localhost:3000/');
});
JS

# サーバー起動
node server.js

# 別ターミナルでテスト
curl http://localhost:3000/
curl http://localhost:3000/api/time
```

### Netcat - 汎用ネットワークツール

```bash
# インストール
sudo apt install netcat -y

# TCPサーバー起動
nc -l -p 12345

# TCPクライアント接続
nc localhost 12345

# ポートスキャン
nc -zv localhost 20-100

# ファイル転送
# 受信側：
nc -l -p 12345 > received_file.txt
# 送信側：
nc localhost 12345 < send_file.txt

# 簡易チャットサーバー
# サーバー側：
nc -l -p 12345
# クライアント側：
nc server_ip 12345
```

## 4.5 ファイアウォール基礎

### ufw - 簡易ファイアウォール

```bash
# インストールと有効化
sudo apt install ufw -y

# 状態確認
sudo ufw status

# 基本ポリシー設定
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 特定ポート許可
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 特定IPからのみ許可
sudo ufw allow from 192.168.1.100 to any port 22

# ルール削除
sudo ufw delete allow 80/tcp

# 有効化（WSL2では通常不要）
sudo ufw enable
```

### iptables - 詳細設定

```bash
# 現在のルール表示
sudo iptables -L -n -v

# 特定ポートを開く
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# 特定IPからの接続を拒否
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# ルール保存（再起動後も維持）
sudo apt install iptables-persistent -y
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

# 2. IPアドレス確認
echo -e "\n2. IP Addresses:"
ip -4 addr show | grep inet | grep -v 127.0.0.1

# 3. デフォルトゲートウェイ確認
echo -e "\n3. Default Gateway:"
ip route | grep default

# 4. DNS確認
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
| 外部から接続できない | タイムアウト | Windows Firewall確認 |
| DNS解決失敗 | `cannot resolve host` | `/etc/resolv.conf`確認 |
| ポート既に使用中 | `Address already in use` | `lsof -i :PORT`で確認 |
| WSL2 IP変更 | 接続先不明 | `hostname -I`で再確認 |

### WSL2特有の問題対処

```bash
# Windows Defenderファイアウォール例外追加（PowerShell管理者）
New-NetFirewallRule -DisplayName "WSL2 Port 8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow

# WSL2のIP自動取得スクリプト
cat << 'SCRIPT' > ~/get_wsl_ip.sh
#!/bin/bash
# WSL2 IP取得
WSL_IP=$(hostname -I | awk '{print $1}')
WIN_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')

echo "WSL2 IP: $WSL_IP"
echo "Windows IP (from WSL2): $WIN_IP"

# Windowsのhostsファイル更新用
echo "Add to C:\\Windows\\System32\\drivers\\etc\\hosts:"
echo "$WSL_IP wsl.local"
SCRIPT

chmod +x ~/get_wsl_ip.sh
```

## 4.7 演習問題

### 演習1: ポート監視スクリプト

```bash
#!/bin/bash
# port_monitor.sh - 指定ポートの監視

PORTS="22 80 443 3306 5432"
LOG_FILE="/var/log/port_monitor.log"

echo "=== Port Monitoring Report ===" | tee -a $LOG_FILE
echo "Date: $(date)" | tee -a $LOG_FILE

for port in $PORTS; do
    if ss -tln | grep -q ":$port "; then
        service=$(ss -tlnp 2>/dev/null | grep ":$port " | awk '{print $NF}' | cut -d'"' -f2)
        echo "✓ Port $port is open (Service: ${service:-unknown})" | tee -a $LOG_FILE
    else
        echo "✗ Port $port is closed" | tee -a $LOG_FILE
    fi
done
```

### 演習2: 簡易ロードバランサー

```bash
#!/bin/bash
# simple_lb.sh - 簡易ラウンドロビン

BACKENDS=("localhost:8001" "localhost:8002" "localhost:8003")
CURRENT=0

# バックエンドサーバー起動
for i in {1..3}; do
    port=$((8000 + i))
    mkdir -p ~/backend$i
    echo "<h1>Backend Server $i</h1>" > ~/backend$i/index.html
    (cd ~/backend$i && python3 -m http.server $port) &
done

# ロードバランサー
while true; do
    nc -l -p 8000 -c "curl -s ${BACKENDS[$CURRENT]}"
    CURRENT=$(( (CURRENT + 1) % ${#BACKENDS[@]} ))
done
```

### 演習3: API監視とアラート

```bash
#!/bin/bash
# api_health_check.sh - API死活監視

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
        echo "$(date): ✗ $url is down (HTTP $response)" | tee -a /var/log/api_alerts.log
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
sudo apt install iperf3 -y

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
sudo apt install mtr -y
mtr google.com

# 統計情報のみ
mtr -r -c 100 google.com
```

### HTTP応答時間測定

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

ネットワーク管理の要点：

1. **WSL2の特性理解**: NAT構造とポートフォワーディング
2. **基本ツール習得**: ping、curl、ss の日常的使用
3. **トラブルシューティング**: 段階的な問題切り分け手法

次章では、これらの知識を活用してシェルスクリプトによる自動化を学習します。
