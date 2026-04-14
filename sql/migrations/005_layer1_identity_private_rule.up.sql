BEGIN;

SET search_path TO topomemory, public;

ALTER TABLE identity_decision
  DROP CONSTRAINT identity_decision_type_valid;

ALTER TABLE identity_decision
  ADD CONSTRAINT identity_decision_type_valid CHECK (
    decision_type IN (
      'matched_existing_entity',
      'new_entity_created',
      'skipped_private_scope',
      'skipped_no_public_ip',
      'skipped_hostname_weak',
      'skipped_hostname_conflict',
      'skipped_private_insufficient_context',
      'skipped_private_conflict'
    )
  );

COMMENT ON CONSTRAINT identity_decision_type_valid ON identity_decision IS 'Tipos auditáveis da identidade mínima, incluindo a regra determinística conservadora para IP privado.';

COMMIT;
