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


## 2026-10-12 — M1.1: visualizador/editor alfa de malhas de colisão (ChatGPT)
- **Objetivo:** permitir modificação local da geometria física extraída no Poco X8 Pro, sem alterar APK original.
- **Arquivos criados:** `web/index.html`, `web/app.js`, `web/collision_core.js`, `tools/export_collision.py`, `tests/test_collision.py`, `tests-js/collision.test.cjs`, `docs/EDITOR_ANDROID.md`.
- **Método:** analisar prefixo de malhas `VuCollisionMeshAsset/Level`: u32 quantidade de vértices, N×(x,y,z,w float32), u32 quantidade de índices, índices u16 e região ainda desconhecida. Criar ferramenta para extrair apenas recursos cujas contagens e referências são coerentes. No frontend, manipular apenas float32 de coordenadas, mantendo todos os outros bytes da cópia.
- **Evidências:** 80 de 87 malhas passaram interpretação estrutural; outras 7 apresentaram diferença de 1 byte entre saída e tamanho declarado e permaneceram não verificadas. Em `CityA/Zone01_col`, 951 vértices e 1620 triângulos. Exportação local das 9 malhas de `CityA` validada.
- **Testes:** 9 testes Python sintéticos passaram; suíte de testes JS passou; `node --check` passou. Ainda sem validação de funcionamento da página em navegador Android real.
- **Limites:** editor altera uma cópia do arquivo binário de colisão, **não** o APF/APK instalável; não move modelos renderizados nem sincroniza estruturas auxiliares de colisão. Não afirmar pista jogável.

## 2026-10-12 — M1.2: GitHub Pages, HTML portátil e checagem PairIP (ChatGPT)
- **Objetivo:** oferecer interface acessível pelo Android sem exigir servidor local e entender riscos de alteração do APK.
- **Mudanças:** criada a branch `gh-pages` com `index.html`, `app.js`, `collision_core.js`, `editor-offline.html` e `.nojekyll`. Adicionado `web/editor-offline.html` na branch principal; HTML único incorpora scripts JavaScript inline e pode ser aberto localmente sem hospedagem.
- **Como:** sincronização dos scripts da interface da branch `main` para `gh-pages`; verificação de ausência de `<script src>` no HTML portátil; GitHub Pages deve ser configurado como `gh-pages` + `/(root)` em Settings → Pages, pois a conexão atual não disponibiliza API de ativação.
- **Evidência PairIP:** na cópia XAPK, encontrado `lib/arm64-v8a/libpairipcore.so` dentro de `split_config.arm64_v8a.apk`. Presença não prova que todas as verificações de integridade estejam ativas; Google descreve checks anti-tamper e de instalador. Nenhuma tentativa de modificação de proteção foi realizada.
- **Testes:** `node --check` do JS e 9 testes Python + suíte JS passaram localmente; arquivo HTML único criado e verificado quanto à ausência de dependências externas de script. GitHub Pages **ainda não foi confirmado como publicado/ativo**, requer ação do proprietário nas configurações. Não foi realizado teste real no Chrome Android.
- **Próximos passos:** conferir acessibilidade do Pages após habilitação; testar seleção/edição no navegador do Poco; compreender dados desconhecidos nas malhas, vínculos de modelos visuais e integridade do APF. Não compartilhar binários do jogo.
