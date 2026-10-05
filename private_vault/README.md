# Private Vault

The bundled public demo files are in `private_vault/documents/`. Authenticated users' private `.txt`, `.md`, and `.pdf` files belong in `private_vault/documents/users/<user_id>/documents/`; the authenticated index rebuild only processes that user's vault. Source documents stay local and private vault contents must not be committed.

The `processed/` directory is reserved for local processing artifacts and is not required for normal searching.