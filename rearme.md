# Diário de alterações obrigatório — rearme.md

Registrar toda alteração com **data, agente, objetivo, arquivos, método, evidência, testes e limitações**. Também detalhar investigação no `docs/RESEARCH_LOG.md`.

## 2026-10-12 — M0: inspeção estática inicial (ChatGPT)
- **Objetivo:** descobrir onde estão dados das pistas sem modificar o jogo.
- **Método:** inspecionar o XAPK do proprietário e localizar `base.apk/assets/Assets.apf`; percorrer índice `FPUV` v6 em modo leitura; testar zlib e LZMA1 raw em cinco amostras.
- **Resultado:** índice de 3294 entradas a partir de 88909047 (200079 bytes); nomes de nove ambientes e recursos de cena, colisão e água. Strings citam `VuAiWaypointEntity` e checkpoints.
- **Testes:** quatro testes sintéticos passaram em ambiente local; cinco recursos reais descompactados, com tamanho validado.
- **Limitação:** não existe editor, repacker ou mapa customizado funcional.

## 2026-10-12 — M0.1: comparação independente do extrator Claude (ChatGPT)
- **Método:** carregar a mesma cópia APF com o script `riptide_apf_extractor.py` enviado pelo Claude e com o leitor do ChatGPT, comparar o índice completo e os bytes extraídos.
- **Resultado:** todas as 3294 entradas têm nomes/offsets/tamanhos idênticos. Bytes idênticos em `Assets/AssetData` (92265), `VuTemplateAsset/Levels/CityA` (1198119), `VuTemplateAsset/Levels/ParkA` (3057174), `VuWaterMapAsset/CityA/WS01` (8358), `VuCollisionMeshAsset/Level/CityA/Zone01_col` (79725).
- **Riscos encontrados:** script Claude consome ~89 MB de RAM para carregar APF, não valida todas as fronteiras, pode gravar nomes de arquivo inseguros; campo `crc` e hash de cabeçalho ainda não tiveram algoritmos comprovados.
- **Decisão:** manter análise read-only, endurecer extrator antes de gravar arquivos.

## 2026-10-12 — M0.2: GitHub compartilhado (ChatGPT)
- **Objetivo:** permitir trabalho auditável de agentes.
- **Alterações:** repositório inicial, README, instruções Claude, documentação, testes e issue de coordenação.
- **Política:** publicar apenas código e metadados, não o XAPK original.
- **Limitação:** mensagens entre agentes são assíncronas, via issues revisadas quando solicitadas.

## Próximo registro
Agente / data / issue-PR / hipótese / procedimento / evidência / falhas / testes / arquivos modificados / pendências.
