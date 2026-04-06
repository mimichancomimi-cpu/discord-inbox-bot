---
nexus: nexus-ai-chat-importer
plugin_version: "1.3.3"
provider: chatgpt
aliases: Obsidian同期方法と使い方
conversation_id: 696fa777-a424-8327-bb88-063f9fb79697
create_time: 2026-01-20T16:04:23.910Z
update_time: 2026-01-20T16:06:49.903Z
---

# Title: Obsidian同期方法と使い方

Created: 2026/01/21 at 01:04:23
Last Updated: 2026/01/21 at 01:06:49
Chat URL: https://chatgpt.com/c/696fa777-a424-8327-bb88-063f9fb79697


>[!nexus_user] **User** - 2026/01/21 at 01:04:23
> iPhoneのアプリ、オブシディアンを入れたんだけど使い方を教えて。PCと同期させたい
<!-- UID: 0f05da48-30a9-43ad-b438-550adf1df860 -->
>[!nexus_agent] **Assistant** - 2026/01/21 at 01:04:23
> 了解。 
> 「iPhoneのObsidianをどう使うか」と「PCとどう同期するか」は**最初に正しく設計するかどうかで、使いやすさが大きく変わる**ので、順番に丁寧に説明します。
>
> ---
>
> ## ① Obsidianの基本構造（最重要）
>
> まず前提から。
>
> ### Obsidianは「アプリ」ではなく「フォルダを見るソフト」
> - Obsidianは **Markdown（.md）ファイル** を扱う
> - ノートは全部「普通のフォルダ」に保存される
> - そのフォルダを **PC・iPhoneの両方から見られる状態** にすると同期完了
>
> イメージ 
> ```
> 📁 Obsidian用フォルダ
>  ├─ メモ1.md
>  ├─ アイデア.md
>  └─ 日記.md
> ```
>
> この「📁フォルダ」をどう同期させるかが核心。
>
> ---
>
> ## ② PCとiPhoneを同期させる方法（3択）
>
> ### 方法① Obsidian公式Sync（いちばん簡単・有料）
> **おすすめ度：★★★★★（迷ったらこれ）**
>
> - 月額：約10ドル
> - 設定が圧倒的にラク
> - iPhone / Mac / Windows すべて自動同期
> - 暗号化あり・速度も安定
>
> #### 手順（超簡単）
> 1. PC版Obsidianをインストール
> 2. Obsidianアカウント作成
> 3. 「Settings → Obsidian Sync」をON
> 4. iPhoneでも同じアカウントでログイン
>
> → 即同期
>
> **向いている人**
> - 思考整理・仕事・発信で使いたい
> - トラブル対応したくない
> - 時間をお金で買える
>
> ---
>
> ### 方法② iCloud同期（無料・Appleユーザー向け）
> **おすすめ度：★★★★☆（Mac＋iPhoneなら現実的）**
>
> #### 構成
> - Mac：iCloud Drive
> - iPhone：iCloud Drive
> - 同じフォルダを指定
>
> #### 手順
> **Mac側**
> 1. iCloud DriveをON
> 2. `iCloud Drive/Obsidian` フォルダを作成
> 3. ObsidianでそのフォルダをVaultとして指定
>
> **iPhone側**
> 1. Obsidianを開く
> 2. 「Open folder as vault」
> 3. iCloud Drive → Obsidianフォルダを選択
>
> #### 注意点（重要）
> - 同時編集に弱い
> - 同期が遅れることがある
> - たまに競合ファイルが出る
>
> **向いている人**
> - Mac＋iPhoneのみ
> - 無料で使いたい
> - 多少の不具合は許容できる
>
> ---
>
> ### 方法③ Git / Dropbox（上級者向け）
> 今回は割愛。 
> 最初から選ぶ必要はありません。
>
> ---
>
> ## ③ iPhone版Obsidianの基本操作
>
> ### ノート作成
> - 右下「＋」 → New note
> - Markdownで普通に文章を書く
>
> ### よく使う記法（最低限）
> ```
> # 見出し
> ## 小見出し
>
> - 箇条書き
> - 箇条書き
>
> [[他のノート名]] ← リンク
> ```
>
> ### 内部リンクがObsidianの強み
> ```
> [[Threadsアイデア]]
> [[占い鑑定テンプレ]]
> ```
> → ノート同士が勝手につながる
>
> ---
>
> ## ④ 最初に入れておくと便利な設定（iPhone）
>
> ### 設定 → Editor
> - 「Readable line length」ON（読みやすい）
> - 「Live Preview」ON
>
> ### 設定 → Files & Links
> - New link format：Relative path
> - Default location for new notes：同じフォルダ
>
> ---
>
> ## ⑤ どう使うと「強い思考ツール」になるか
>
> mimiちゃんの用途的におすすめなのはこの3つ。
>
> ### ① アイデアの保管庫
> - Threadsネタ
> - note構成案
> - 企画の種
>
> ### ② 思考の分解ノート
> - 「なぜ伸びたか」
> - 「なぜ刺さったか」
> - 感情 → 構造 →再現性
>
> ### ③ 資産化ノート
> - テンプレ
> - 言い回し
> - 型
>
> Obsidianは 
> **「書くため」より「考えを育てるため」**のツール。
>
> ---
>
> ## ⑥ 結論：おすすめ構成
>
> 迷わない答えを出します。
>
> - **本気で使う → Obsidian公式Sync**
> - **無料で試す → iCloud同期**
>
> ---
>
> ## 次にできること
> もしよければ次は：
> - フォルダ構成テンプレ（mimiちゃん用）
> - Threads / note / 占い用のノート設計
> - 「散らからないObsidianの使い方」
>
> どれを知りたいか教えてください。
<!-- UID: b4c22970-70af-4dfa-abf5-efd73104f7f8 -->

---
>[!nexus_agent] **Assistant** - 2026/01/21 at 01:05:03
> この画面は **「最初の保管場所（Vault）をどうするか」** を選ぶところです。 
> ここでの選択が、そのまま **PCと同期できるかどうか** に直結します。
>
> 状況別に、**今この画面でどれを押すべきか**をはっきり説明します。
>
> ---
>
> ## 結論から
>
> ### まだPC側にObsidianがない／同期方法を決めていない 
> → **今は「Create a vault」を押してOK**
>
> あとからPCと同期できます。 
> これは「仮の箱」を作るだけなので失敗ではありません。
>
> ---
>
> ## それぞれのボタンの意味
>
> ### ① Create a vault（紫のボタン）
> **＝ 新しくノート用フォルダを作る**
>
> - iPhone内に新しいVaultを作る
> - まだPCとはつながっていない
> - 後から
>  - Obsidian Sync
>  - iCloud
>  に切り替え可能
>
> **初心者はまずこれでOK**
>
> ---
>
> ### ② Use my existing vault（グレーのボタン）
> **＝ すでに存在するフォルダを使う**
>
> これは下のどちらかの場合のみ使います。
>
> - すでに
>  - iCloud Drive に Obsidianフォルダがある
>  - PCで作ったVaultをiPhoneで開きたい
> - 同期設計がすでに終わっている
>
> 今の状況だと、まだ使わなくていい可能性が高いです。
>
> ---
>
> ## 今おすすめの進め方（迷わない手順）
>
> ### ステップ1（今）
> 1. **Create a vault** を押す
> 2. 名前を聞かれたら 
>  例：
>  - `mimi-notes`
>  - `Obsidian`
>  - `thinking-vault`
> 3. 保存場所は **iPhone内（Local）でOK**
>
> → まず書ける状態を作る
>
> ---
>
> ### ステップ2（あとで）
> PC側でObsidianを入れたら、どちらか選ぶ：
>
> #### パターンA：公式Syncを使う
> - Settings → Obsidian Sync → ON
> - 同じアカウントでPCログイン
> - 自動で同じVaultが出てくる
>
> #### パターンB：iCloud同期に切り替える
> - iCloud Drive にVaultを移動
> - PC側でも同じフォルダを指定
>
> ---
>
> ## よくある不安への答え
>
> ### Q. 今Createしたら失敗？
> → **全く失敗じゃない**
>
> Vaultは「ただのフォルダ」なので 
> あとから移動・同期・切り替え自由。
>
> ### Q. ノート消えない？
> → 消えません 
> Obsidianは削除しない限りデータは残ります。
>
> ---
>
> ## まとめ（ここだけ覚えて）
>
> - 今は **Create a vault を押してOK**
> - 名前をつけて進むだけ
> - 同期は後からいくらでもできる
>
> ---
>
> 次に進んだら 
> - 「名前どうしたらいい？」
> - 「保存場所の画面が出た」
> - 「次の画面これなんだけど」
>
> そのままスクショ投げてくれて大丈夫です。 
> 画面見ながら一緒に進めます。
<!-- UID: 63fa4d3e-3188-4453-8ba7-bed424f8532c -->

---
>[!nexus_user] **User** - 2026/01/21 at 01:05:34
> PCにもうオブシディアンはあります
<!-- UID: e41c8da2-2de2-4965-b0fd-e409e96f96c2 -->
>[!nexus_agent] **Assistant** - 2026/01/21 at 01:05:36
> OK、状況ははっきりしました。 
> **PCにすでにObsidianがある＝そのPCのVaultをiPhoneで開く**のが正解です。
>
> 今表示されているその画面では、**やることは1つ**です。
>
> ---
>
> ## 今この画面でやること（結論）
>
> 👉 **「Use my existing vault」** を押してください。
>
> これは 
> 「PCで使っているVaultを、iPhoneでも使いますか？」 
> という意味です。
>
> ---
>
> ## ここから先の正しい手順（iPhone側）
>
> ### ①「Use my existing vault」をタップ
> ↓ 
> ### ② 保存場所を聞かれる
>
> ここで分岐します。
>
> ---
>
> ## A：PCと iCloud で同期している場合（Mac）
>
> もしPC（Mac）のObsidianが 
> **iCloud Drive内のフォルダ**をVaultにしているなら：
>
> 1. **iCloud Drive** を選ぶ 
> 2. PCで使っている 
>  `Obsidian` や `mimi-notes` などのフォルダを選択 
> 3. 「Open」や「許可」
>
> → **即、PCと同じノートが表示されます**
>
> ---
>
> ## B：PCがWindows / iCloudを使っていない場合
>
> その場合、今はまだiPhoneから直接は開けません。
>
> この場合は一度止まってOKなので、教えてください。
>
> - PCは **Mac / Windows どっち？**
> - PC側のVaultは 
>  - iCloud 
>  - Dropbox 
>  - ローカルのみ 
>  どれ？
>
> それによって最適ルートが変わります。
>
> ---
>
> ## 重要な注意点（ここだけ必ず）
>
> - **Create a vault は今回は押さない**
>  → それを押すと「別のVault」ができてしまう
> - 「Use my existing vault」は 
>  **既存のフォルダを“見る”だけ**なので安全
>
> ---
>
> ## もし今つまずいたら
>
> 次の画面をそのままスクショして送ってください。 
> - 保存場所選択画面 
> - iCloud Driveの中身 
> - エラー表示
>
> 画面ベースで「ここ押す」をピンポイントで案内します。
>
> ---
>
> まずは今、 
> **Use my existing vault をタップ** 
> → 次の画面を見せてください。
<!-- UID: 3bf8dabd-0e09-4aeb-aa60-e2f815a00889 -->

---
>[!nexus_agent] **Assistant** - 2026/01/21 at 01:06:17
> この画面、**よく出ます。原因も対処もはっきりしています。** 
> 順番に整理します。
>
> ---
>
> ## いま出ているエラーの意味（超重要）
>
> 表示文を日本語にするとこうです。
>
>> iCloud上に Obsidian のVaultが見つかりません 
>> 理由として考えられるのは 
>> 1. 別のiCloudアカウントにある 
>> 2. iCloud Drive直下の「Obsidian」フォルダに置かれていない
>
> **結論** 
> 👉 **PC側のVaultが、iCloud Driveの正しい場所にない** 
> それだけです。
>
> ---
>
> ## つまり今の状態
>
> - PCには Obsidian がある 
> - でもそのVaultは 
>  - ローカルフォルダ 
>  - もしくは iCloud内でも「Obsidianフォルダ直下」ではない 
> - だから iPhone から見えない
>
> **データが消えたわけでも、失敗でもありません。**
>
> ---
>
> ## 正解ルート（Mac＋iPhone想定）
>
> ### やることは「PC側」で1回だけ
>
> #### ① Macで Finder を開く
> #### ② iCloud Drive を開く
> #### ③ その中に **Obsidian というフォルダを作る**
> （名前は正確に `Obsidian`）
>
> 構造はこう：
> ```
> iCloud Drive
>  └─ Obsidian
>  └─ あなたのVaultフォルダ
>  ├─ ノート.md
>  └─ フォルダ…
> ```
>
> ---
>
> ### ④ PCのObsidianでやること
>
> 1. Obsidianを開く
> 2. 左下の **Vault切り替え（フォルダアイコン）**
> 3. 「Open another vault」
> 4. **今作った iCloud Drive / Obsidian / Vaultフォルダ を指定**
>
> ここで 
> 👉 **PCのObsidianがiCloud上のVaultを見る状態**になります。
>
> ---
>
> ## ここまで終わったら（iPhone側）
>
> 1. iPhoneのObsidianを一度閉じる
> 2. 再度起動
> 3. **Use my existing vault**
> 4. iCloud → Obsidian フォルダ
>
> → **今度は必ず表示されます**
>
> ---
>
> ## よくある勘違い（安心ポイント）
>
> - Vault名は何でもいい 
> - 重要なのは 
>  **「iCloud Drive / Obsidian / Vault」という階層**
> - 中身をコピーしてもOK（移動が不安ならコピー）
>
> ---
>
> ## もしPCがWindowsだった場合
>
> その場合は iCloud同期がそもそも相性悪いので、
> - Obsidian公式Sync 
> - Dropbox 
> の方が安全です。
>
> その場合は手順が変わるので、 
> **PCは Mac / Windows どっちか**だけ教えてください。
>
> ---
>
> ## まとめ（ここだけ）
>
> - エラーの原因：**iCloudの場所が違う**
> - 解決策： 
>  **PCで iCloud Drive / Obsidian フォルダを作り、そこにVaultを置く**
> - データは一切失われていない
>
> ---
>
> 次にやることは 
> 👉 **PC側でiCloud Driveを開く**
>
> もしその画面で 
> 「どのフォルダがVaultかわからない」 
> 「今どこにあるかわからない」 
> となったら、PC側の画面をそのまま送ってください。 
> そこから一緒に辿ります。
<!-- UID: 8af14586-7221-410e-bbf9-bd5a730bdcdd -->

---