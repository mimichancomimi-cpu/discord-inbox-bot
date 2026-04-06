# 画像の集約・参照更新

Obsidian ボールト（このリポジトリのルート＝`Documents` フォルダ）内の画像を `attachments/` にまとめたり、参照を `![[attachments/…]]` に揃えます。

## 使い方

リポジトリルートで:

```bash
python3 tools/vault-image-utils/consolidate_images.py
python3 tools/vault-image-utils/update_image_refs.py
```

実行前にバックアップまたはコミットを推奨します。
