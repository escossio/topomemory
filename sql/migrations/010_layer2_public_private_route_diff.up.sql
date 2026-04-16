BEGIN;

SET search_path TO topomemory, public;

ALTER TABLE route_snapshot
  ADD COLUMN IF NOT EXISTS public_resolved_path_signature TEXT,
  ADD COLUMN IF NOT EXISTS private_resolved_path_signature TEXT,
  ADD COLUMN IF NOT EXISTS destination_stable_key TEXT,
  ADD COLUMN IF NOT EXISTS public_element_count_resolved INTEGER,
  ADD COLUMN IF NOT EXISTS private_element_count_resolved INTEGER;

ALTER TABLE route_snapshot
  ADD CONSTRAINT route_snapshot_public_resolved_counts_non_negative CHECK (
    public_element_count_resolved IS NULL OR public_element_count_resolved >= 0
  ),
  ADD CONSTRAINT route_snapshot_private_resolved_counts_non_negative CHECK (
    private_element_count_resolved IS NULL OR private_element_count_resolved >= 0
  ),
  ADD CONSTRAINT route_snapshot_resolved_scope_balance CHECK (
    public_element_count_resolved IS NULL
    OR private_element_count_resolved IS NULL
    OR public_element_count_resolved + private_element_count_resolved = total_resolved_elements
  );

ALTER TABLE route_health_assessment
  ADD COLUMN IF NOT EXISTS public_change_status TEXT,
  ADD COLUMN IF NOT EXISTS private_change_status TEXT,
  ADD COLUMN IF NOT EXISTS destination_change_status TEXT;

ALTER TABLE route_health_assessment
  ADD CONSTRAINT route_health_assessment_public_change_status_valid CHECK (
    public_change_status IS NULL OR public_change_status IN ('unchanged', 'changed', 'not_comparable')
  ),
  ADD CONSTRAINT route_health_assessment_private_change_status_valid CHECK (
    private_change_status IS NULL OR private_change_status IN ('unchanged', 'changed', 'not_comparable')
  ),
  ADD CONSTRAINT route_health_assessment_destination_change_status_valid CHECK (
    destination_change_status IS NULL OR destination_change_status IN ('same_destination', 'changed_destination', 'unknown_destination', 'not_comparable')
  );

COMMENT ON COLUMN route_snapshot.public_resolved_path_signature IS 'Assinatura ordenada do trecho público resolvido da rota.';
COMMENT ON COLUMN route_snapshot.private_resolved_path_signature IS 'Assinatura ordenada do trecho privado resolvido da rota.';
COMMENT ON COLUMN route_snapshot.destination_stable_key IS 'Chave estável simples do destino final para comparação entre runs.';
COMMENT ON COLUMN route_snapshot.public_element_count_resolved IS 'Quantidade de elementos públicos resolvidos no snapshot.';
COMMENT ON COLUMN route_snapshot.private_element_count_resolved IS 'Quantidade de elementos privados resolvidos no snapshot.';
COMMENT ON COLUMN route_health_assessment.public_change_status IS 'Status de mudança do trecho público resolvido.';
COMMENT ON COLUMN route_health_assessment.private_change_status IS 'Status de mudança do trecho privado resolvido.';
COMMENT ON COLUMN route_health_assessment.destination_change_status IS 'Status da estabilidade do destino final entre runs.';

COMMIT;
