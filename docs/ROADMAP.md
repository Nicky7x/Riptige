# Roadmap técnico

- **M0 — validado:** índice APF v6 e 3294 recursos; zlib/LZMA raw; verificação cruzada dos extratores.
- **M1 — pendente:** parser read-only de `VuTemplateAsset/Levels/CityA` e comparações `ParkA` / `FactoryA`; identificar classes de entidades, offsets e referências.
- **M2 — pendente:** mapear relações entre `VuWorkspaceAsset`, `VuProjectAsset`, `VuStaticModelAsset`, `VuCollisionMeshAsset` e `VuWaterMapAsset`.
- **M3 — pendente:** demonstrar round-trip byte-idêntico em arquivo *copiado*, descobrir campos desconhecidos e integridade; só então investigar reempacotamento.
- **M4 — pendente:** teste offline de uma alteração pequena com backup.
- **M5 — pendente:** editor de pistas, geometria e arte originais, física/água/colisões, waypoints e checkpoints, seleção e carregamento.

**Critério de conclusão:** resultados testados, evidência reproduzível e limites documentados. Não apresentar inferência como fato.
