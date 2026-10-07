-- ETHAN PostgreSQL migration 009
-- Garantie d'intégrité : UN SEUL provider peut être `is_default`.
--
-- Audit §4 — le provider par défaut était choisi en mémoire et mis en cache
-- Redis : il repartait du premier provider actif à chaque refresh WebUI, et ne
-- survivait ni à un restart ni à un recreate de l'API. La colonne `is_default`
-- existe déjà (migration 004), mais rien n'empêchait plusieurs lignes de
-- revendiquer le défaut simultanément.
--
-- On normalise d'abord l'existant (on garde le marquage le plus récent), puis
-- on pose la contrainte partielle UNIQUE. Sans cette normalisation, la création
-- de l'index échouerait sur un volume déjà corrompu.

\set ON_ERROR_STOP on
BEGIN;

UPDATE llm_providers
   SET is_default = FALSE
 WHERE is_default
   AND provider_id <> (
       SELECT provider_id
         FROM (
               SELECT provider_id, updated_at
                 FROM llm_providers
                WHERE is_default
                ORDER BY updated_at DESC, provider_id
                LIMIT 1
              ) AS keep
   );

-- Index partiel : seules les lignes `is_default = TRUE` sont indexées, avec
-- pour clé la valeur elle-même → une seule ligne peut porter ce défaut.
CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_providers_single_default
    ON llm_providers (is_default)
    WHERE is_default;

INSERT INTO schema_migrations (version)
VALUES ('009_unique_default_provider')
ON CONFLICT (version) DO NOTHING;

COMMIT;
