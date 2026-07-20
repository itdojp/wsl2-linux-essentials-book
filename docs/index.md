---
layout: book
title: "WSL2 Linux実践ガイド"
description: "illustrated-linux-basics-book の次のステップとして、WSL2 上で実践的な Linux スキルを習得するための技術書"
author: "株式会社アイティードゥ"
version: "2.0.1"
---

# WSL2 Linux実践ガイド

このページは、`illustrated-linux-basics-book` の次のステップとして、WSL2 上で実践的な Linux スキルを習得するための公開版の入口です。

## 本書の位置づけ

- **前提書籍**: [illustrated-linux-basics-book](https://itdojp.github.io/illustrated-linux-basics-book/)（初級）
- **本書**: 実践的な Linux スキルの習得（中級）
- **次の書籍**: [linux-infra-textbook2](https://itdojp.github.io/linux-infra-textbook2/)（上級）

### この本を読み終えるとできること

- Windows 上の WSL2 環境で、Ubuntu を使った開発・検証ができる。
- 基本的なファイル操作、テキスト処理、プロセス／サービス管理、ネットワーク確認をコマンドラインで行える。
- **必須経路**を終えると、簡単なシェルスクリプトを書き、学習用データを使った日常作業の自動化を試せる。
- **発展経路**まで終えると、監視・バックアップ・cron・deploy例の適用条件を説明し、隔離した演習環境で検証できる。
- **WordPress経路**まで終えると、学習用の LAMP 環境を構築し、WordPress サイトを立ち上げて検証できる。

## 読み方ガイドと学習経路

| 経路 | 必須範囲 | 任意範囲 | 到達条件 | 計画時間 |
|---|---|---|---|---:|
| 復習込みの必須経路 | 第0〜4章、第5章基礎編 | 第5章発展編、第6章 | local環境でprocess・service・networkを確認し、基本scriptを作成できる | hands-on 7〜11時間 |
| 基礎既習者の必須経路 | 第0・3・4章、第5章基礎編 | 第1・2章、第5章発展編、第6章 | 下のskip判定を満たし、同じ必須経路の到達条件を満たす | hands-on 5〜8時間 |
| 全演習経路 | 第0〜6章、第5章発展編 | LAN公開runbookの実行 | 発展scriptのriskを説明し、WordPressを学習環境で構築・cleanupできる | hands-on 10〜17時間 |

### 第1〜2章のskip判定

`illustrated-linux-basics-book`修了者または同等の経験があり、次の4項目を資料なしで安全に実施・説明できる場合は、第1〜2章を任意の復習としてskipできます。1項目でも不確かな場合は、該当節を実行してから第3章へ進みます。

- `$HOME`配下の使い捨てdirectoryで、fileの作成・copy・move・削除を行い、操作対象を実行前に確認できる。
- `rwx`、owner/group/other、相対pathと絶対pathを説明し、再帰的な権限変更を無条件に実行しない。
- editorでfileを開いて保存・終了し、`diff`で変更内容を確認できる。
- `grep`、pipe、`sort`、`uniq`の基本用途を説明し、sample textから必要な行を抽出できる。

### 章別の計画値

「読むだけ」はbuild済み本文の空白除外文字数を400〜600文字/分で割った再計算値です。「hands-on」は各章のcommand・exercise inventoryを1回確認して設定した初回計画rangeであり、実測保証値ではありません。

| 範囲 | 扱い | 読むだけ | hands-on | 到達条件 |
|---|---|---:|---:|---|
| 第0章 | 環境未構築なら必須 | 4〜6分 | 30〜60分 | WSL version・distribution・状態を確認できる |
| 第1章 | skip条件付き | 10〜15分 | 45〜75分 | file・permission・helpを安全に扱える |
| 第2章 | skip条件付き | 12〜18分 | 60〜90分 | editor・filter・pipe・diffを使える |
| 第3章 | 必須 | 19〜29分 | 75〜120分 | processとserviceを区別し、logで一次切り分けできる |
| 第4章 | 必須 | 41〜61分 | 90〜150分 | local bindを確認し、LAN公開の追加保護を説明できる |
| 第5章 基礎編（5.1〜5.7） | 必須 | 10〜15分 | 90〜150分 | 変数・分岐・loop・function・終了statusを使える |
| 第5章 発展編（5.8〜5.10） | 任意 | 11〜16分 | 120〜240分 | monitoring・backup・cron・root/deploy例のriskを説明できる |
| 第6章 | 任意 | 14〜20分 | 60〜120分 | 学習用WordPressを構築し、到達確認できる |

## 所要時間の定義と算定方法

- **読むだけ**: 公開top・第0〜6章・用語集の`article.page-content`からvisible textを抽出し、空白を除外した文字数を400〜600文字/分で換算します。code textは読む対象に含め、commandは実行しません。現行snapshotは75,219文字・170 code blocksで、126〜189分（約2〜3時間）です。
- **必須hands-on**: commandを入力し、期待結果とcleanupを確認する時間です。章別rangeの合計を時間単位で切り上げ、基礎既習者は5〜8時間、復習込みは7〜11時間を計画します。
- **全演習込み**: 第5章発展編と第6章のWordPress構築まで行う計画で10〜17時間です。LAN公開runbookは別clientが必要なため任意とし、このrangeへ含めません。
- download速度、machine性能、既存環境、入力速度、troubleshootingでrangeを超える場合があります。研修では受講者の実測値を次回計画へ反映してください。
- 算定snapshotと章別task inventoryの確認日: **2026-07-21**。計算の正本は[`assets/data/learning-time.json`]({{ site.baseurl }}/assets/data/learning-time.json)です。

## 目次

- [第0章: WSL2 セットアップ]({{ site.baseurl }}/chapter0/)
- [第1章: Linux の世界への第一歩]({{ site.baseurl }}/chapter1/)
- [第2章: テキスト処理の基本]({{ site.baseurl }}/chapter2/)
- [第3章: プロセスとサービス管理]({{ site.baseurl }}/chapter3/)
- [第4章: ネットワークの基礎]({{ site.baseurl }}/chapter4/)
- [第5章: シェルスクリプト入門]({{ site.baseurl }}/chapter5/)
- [第6章: WordPress構築]({{ site.baseurl }}/chapter6/)
- [用語集]({{ site.baseurl }}/glossary/)

## 概要

本書は、基礎を学んだ読者が WSL2 環境で手を動かしながら、実践的な Linux スキルへ段階的に進むための教材です。

### 想定読者

- illustrated-linux-basics-bookを終えた方
- Linux の基本コマンドは知っているが、実践経験が少ない方
- Windows で Linux 開発環境を構築したい方
- Web サーバー構築に興味がある方

### 前提知識

- 基本的な Linux コマンド（ls, cd, cp, mv等）
- ファイルとディレクトリの概念
- テキストエディタの基本操作

### 学習成果

- **段階的学習**: 各章に学習目標と到達点を明記
- **実践重視**: 実行条件・期待結果・cleanupを確認してからcommandを試す
- **エラー対処**: よくあるトラブルと解決法を記載
- **選択式プロジェクト**: 任意の全演習経路では最終章でWordPressサイトを構築

## ライセンス

本書は **Creative Commons BY-NC-SA 4.0** ライセンスで公開されています。  
教育・研究・個人学習での利用は可能ですが、商用利用には事前の許諾が必要です。

詳細なライセンス条件: [wsl2-linux-essentials-book/LICENSE.md](https://github.com/itdojp/wsl2-linux-essentials-book/blob/main/LICENSE.md)

## 利用と更新情報

- リポジトリ: [itdojp/wsl2-linux-essentials-book](https://github.com/itdojp/wsl2-linux-essentials-book)
- 更新差分を追う場合は、GitHub の [コミット履歴](https://github.com/itdojp/wsl2-linux-essentials-book/commits/main/) と [PR 一覧](https://github.com/itdojp/wsl2-linux-essentials-book/pulls) を参照してください。
- WSL と Ubuntu の動作差は Windows / ディストリビューションのバージョンで変わるため、実行環境のバージョンも併せて確認してください。

お問い合わせ  
株式会社アイティードゥ（ITDO Inc.）  
Email: [knowledge@itdo.jp](mailto:knowledge@itdo.jp)

---

**著者:** 株式会社アイティードゥ  
**バージョン:** 2.0.1  
**最終更新:** 2026-03-02
{% include page-navigation.html %}
