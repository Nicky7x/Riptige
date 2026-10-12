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


## 2026-10-12 — M1.3: editor pessoal com arenas embutidas (ChatGPT)

- **Objetivo do usuário:** não exigir upload/importação de arquivos na GUI e acelerar a modificação experimental das pistas.
- **Mudança:** novo `tools/build_private_editor.py` gera **localmente**, usando o XAPK/APF original do proprietário, um HTML único com os recursos das arenas pré-embutidos em gzip+base64. `web/bundle_loader.js` apresenta seletores por arena e trecho, estado persistente entre trocas, deslocamento rápido de todos os vértices e exportação consolidada do `riptide-arenas-patch.json`. A `web/app.js` recebeu API `RiptideEditor` e undo/redo de ações em lote.
- **Como foi feito:** ler o índice proprietário `FPUV` v6, descompactar cada `VuCollisionMeshAsset/Level` e validar 4 float32/vértice, índices triangulares e limites. Comprimir apenas os recursos válidos com gzip determinístico e incorporá-los no HTML pessoal, que não depende de servidor nem upload. Recursos proprietários **não foram enviados ao GitHub público**.
- **Resultado confirmado:** **9 arenas e 75 das 87 malhas** validadas e incluídas em HTML privado de **4.553.967 bytes**. Doze malhas foram excluídas por tamanho decodificado divergente (+1 byte em sete casos) ou quarto componente de vértice diferente do esperado (cinco casos). Informação antiga de 80/87 refere-se a outra sondagem/critério e não é o resultado deste carregador mais restritivo.
- **Teste no navegador:** Chromium headless carregou o HTML via `set_content` (navegação `file://` bloqueada pela infraestrutura de teste); selecionou `CityA/CityOldShortcut_col` com **276 vértices**, moveu a malha, alternou para CityB e de volta, verificou que 276 vértices permaneciam alterados, baixou o patch JSON e não encontrou erros JavaScript. **Ainda falta teste em Chrome Android no dispositivo do usuário.**
- **Limitação:** são malhas de colisão, não a geometria visual nem checkpoints/IA. Exportar um patch não muda o APK instalado.

## 2026-10-12 — M1.4: reconstrução experimental de APF a partir dos patches (ChatGPT)

- **Objetivo:** modificar um recurso real no APF, avançando além do editor.
- **Mudança:** criado `tools/apply_arena_patch.py` compatível com XAPK/APK/APF privados; aceita o JSON consolidado, valida coordenadas antigas e novas contra os vértices originais, recomprime os dados LZMA1/zlib, preserva payloads originais não alterados e reescreve os índices e `index_offset` do cabeçalho em uma **cópia do APF**.
- **Teste executado:** aplicado **+0,5 na coordenada Z do vértice 0** de `VuCollisionMeshAsset/Level/CityA/Zone01_col`, a partir do XAPK original. APF original **89.109.126 bytes**; APF experimental **89.127.868 bytes**. O índice do resultado foi analisado novamente: **3.294/3.294 entradas preservadas**, uma única referência de offset mudou e o recurso recomprimido foi decodificado novamente sem erro. O SHA-256 original e novo são diferentes, confirmando modificação do arquivo.
- **Limites técnicos:** campos `header_at_20` e `entry_unknown_u32` e bits restantes das flags não foram decodificados; apesar da estrutura parseável, **não houve teste de execução do jogo**; proteção PairIP foi observada no XAPK e pode recusar um APK modificado. Não alegar que já existe uma pista funcional ou APK pronto para instalar.
- **Próximas tarefas para Claude:** mapear campos desconhecidos e estruturas auxiliares de colisão, descobrir referências visuais/IA no `VuTemplateAsset`, projetar teste in-game autorizado/offline que não contorne DRM.
