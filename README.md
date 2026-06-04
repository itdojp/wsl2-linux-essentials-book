# WSL2 Linux実践ガイド

`illustrated-linux-basics-book` の次のステップとして、WSL2 上でより実践的な Linux スキルを身に付けるための技術書です。

- 公開ページ（GitHub Pages）: [wsl2-linux-essentials-book](https://itdojp.github.io/wsl2-linux-essentials-book/)
- 目次（リポジトリ内）: `docs/index.md`
- シリーズ: [it-engineer-knowledge-architecture](https://github.com/itdojp/it-engineer-knowledge-architecture)

## この本を読み終えるとできること（抜粋）

- Windows 上の WSL2 環境で、Ubuntu を使った開発・検証ができる。
- 基本的なファイル操作・テキスト処理・プロセス／サービス管理・ネットワーク確認がコマンドラインで行える。
- 簡単なシェルスクリプトを書いて、日常作業を自動化できる。
- 学習用の LAMP 環境を構築し、WordPress サイトを立ち上げて試せる。

## ローカル品質確認

公開前の最小確認として、次のコマンドでメタデータ・ナビゲーション・公開ルートの整合性を検証します。

```bash
npm ci
npm test
# または
npm run check:metadata
npm run check:security
```

この検証では `book-config.json`、`package.json`、Jekyll 設定、`docs/_data/navigation.json`、公開対象の `docs/**/*.md`、および必須公開アセットの対応関係を確認します。
`npm run check:security` は `package-lock.json` に基づいて任意依存を除いた npm 依存関係監査を実行します。

## フィードバック（誤り指摘・改善提案）

誤字脱字、技術的な誤り、改善提案は Issues / PR で受け付けます。手順は `CONTRIBUTING.md` を参照してください。

## ライセンス

本書は Creative Commons BY-NC-SA 4.0 で提供されています。詳細は `LICENSE.md` を参照してください。
