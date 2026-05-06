# セキュリティと共有安全性

v1 では、全メンバーが全クライアント・全社内プロジェクトを読める前提です。チーム全体に見せてはいけない素材は、この repository に保存しないでください。

読み取り権限は folder では分けませんが、ローカル hook と CI で更新範囲は分けます。`member` の人が更新できるのは `clients/`、`internal/`、`raw/`、`inbox/` です。skill、tool、docs、template、hook、`company/` など repository 運用側の変更は `developer` または `admin` role の担当者で行います。

## 基本方針

- `events/`、`profile.md`、`sources.md`、`states/current.md` は社内用 memory です。
- `raw/` も社内用 memory です。複数 client / internal を跨ぐ raw 原本を保存できます。
- クライアントに見せる文面は `memory-output` でチャット上に draft として作り、送付前に人間が確認します。
- `inbox/` は local triage です。業務の根拠にする場合は、先に正式 event に昇格します。

## 出してはいけないもの

クライアント向け draft には以下を含めません。

- 別クライアントの情報。
- 社内プロジェクトの内部情報。
- 内部懸念、未確定の推測、未確認の数値。
- クライアントに見せる前提でないメモ。
- `inbox/` にある未昇格メモ。

機械チェックは、entity 配下の file が別 client / internal や raw note を直接参照していないかを確認します。文章として安全かどうかは人間確認、commit 差分確認、GitHub Actions で確認します。

## 今後の強化

client ごとの読み取りアクセス制御が必要になった場合は、機密性の高い client を別 repository に分けるか、encrypted secret store を導入します。folder だけで読み取りアクセス制御を擬似的に表現しないでください。
