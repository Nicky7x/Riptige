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


## 2026-10-12 — M1.5: protótipo 3D com toque (ChatGPT)

- **Solicitação:** evoluir do editor de vértices 2D para um ambiente semelhante a engine mobile, navegável e manipulável com os dedos. Criação automática de pistas por agentes ficará para outra etapa.
- **Código adicionado:** `web/scene3d.js` usa WebGL1 para mostrar os vértices/triângulos originais das malhas de colisão e cores de seleção por malha; seleção por framebuffer de identificação; controles de órbita, zoom/pan com dois dedos e deslocamento de trechos no plano XY. `web/scene3d_fallback.js` realiza renderização por perspectiva/canvas quando WebGL não está disponível, com simplificação de polígonos para desempenho. `web/bundle_loader.js` sincroniza a cena com as arenas já incorporadas, histórico de mudanças e patches. `tools/build_private_editor.py` inclui ambos os renderizadores num único HTML privado.
- **Fonte:** a cópia original do usuário foi lida localmente, em modo leitura, para empacotar malhas autorizadas. Nenhum XAPK, APF, dump de recurso, binário do jogo ou HTML pessoal com dados proprietários foi enviado ao GitHub.
- **Teste real de interface em ambiente controlado:** HTML gerado de **9 arenas e 75 malhas** abriu em Chromium headless configurado com tela e toque mobile. No ambiente de teste, WebGL esteve indisponível, portanto **o fallback Canvas foi efetivamente executado**; WebGL teve verificação de sintaxe, mas ainda **não** teste de renderização real em GPU Android. Cena inicial carregou nove malhas CityA sem erros; controles de órbita, focar, ver arena, troca para CityB/retorno, aplicação de deslocamento Z+0,5 em 951 vértices, preservação do estado e download de patch JSON de 286078 bytes foram verificados.
- **Restrições:** geometria física, não cenário texturizado. Gestos de movimentação de trechos via WebGL/Canvas precisam ser validados no celular real. Não foi criado um APK executável ou uma arena jogável.
- **Próxima ação:** testar desempenho, legibilidade e gestos no Poco X8 Pro; depois decodificar geometria visual para integrar objetos 3D visíveis.


## 2026-10-12 — M1.6: projeto APK Android (ChatGPT)

**Motivo:** o usuário deseja instalar e testar um aplicativo Android, com build automática pelo GitHub Actions, além do editor em HTML.

**Arquivos:** `android/settings.gradle`, `android/build.gradle`, `android/app/build.gradle`, `android/app/src/main/java/com/nicky7x/riptidemaplab/{ApfImporter,MainActivity}.java`, `android/app/src/main/assets/editor_template.html`, `android/app/src/test/.../ApfImporterTest.java`, `README-ANDROID.md`, `.github/workflows/build-android.yml`.

**Abordagem:** Java nativo gerencia SAF (escolha de XAPK e exportação), extração de `base.apk/assets/Assets.apf` em streaming, leitura do índice FPUV v6, descompressão zlib e LZMA1 raw via `org.tukaani:xz`, validação de vértices/triângulos, cache privado por app. O editor original WebGL/Canvas é renderizado numa WebView local. Os scripts no template são incorporados e **nenhum recurso do jogo** foi enviado ao GitHub. Apenas na primeira execução o usuário seleciona seu XAPK original, evitando uploads recorrentes.

**Testes locais executados:** compilação via `javac` do módulo de parser com stubs mínimos de dependências externas, exercício do decodificador zlib com malha sintética e validação de contagem de vértices/triângulos (PASS). HTML sem assets proprietários gerado com único placeholder JSON, renderização numa instância Chromium headless com arena sintética, deslocamento de vértices e exportação de patch (PASS). Isso **não** substitui um teste APK nativo.

**Primeira falha identificada no Actions:** `android-actions/setup-android@v3` tentou instalar pacote removido `tools`, retornando erro antes de compilar. **Correção aplicada:** migrado para `setup-android@v4` com `packages: platform-tools`. Segunda execução disparada para compilar e executar testes JUnit; status de APK depende do resultado.

**Limitações:** APK instalável e compatibilidade no Poco X8 Pro ainda dependem de `assembleDebug` bem-sucedido e teste real. Ainda não existe importação de geometria visual nem suporte a mapas novos dentro do jogo.


## 2026-10-12 — M1.7: primeira compilação APK concluída (ChatGPT)

- **Evidência:** [Actions run #11](https://github.com/Nicky7x/Riptige/actions/runs/38308033274) terminou com status **success**, incluindo `:app:testDebugUnitTest :app:assembleDebug` e publicação do artefato.
- **Resultado físico:** APK `app-debug.apk` de 115296 bytes, SHA-256 `03e2f5bd179acf203c31cb22a4b2fc78689ec06d0011d9033db6694bff5e43e9`, contém `classes.dex`, `AndroidManifest.xml`, `assets/editor_template.html` sem arquivos comerciais; biblioteca LZMA/XZ incorporada no dex.
- **Mudança que resolveu o CI:** `setup-android@v3` instalava pacote SDK `tools` obsoleto e falhava; atualizado para `android-actions/setup-android@v4` com instalação apenas de `platform-tools`. Gradle 8.13/AGP 8.13.2 com Java17 compilou com sucesso.
- **Testes efetivos:** testes unitários sintéticos JUnit passaram no CI, Android debug APK compilado e artefato publicado. Editor web também passou smoke test sintético em navegador. **Não** houve teste em emulador, teste de instalação no Poco ou teste real de XAPK na camada Java/Android. Esses resultados ficam pendentes.


## 2026-10-12 — M1.8: correção de layout e montagem 3D completa (ChatGPT)

**Motivação:** usuário confirmou que o APK v0.1 abre e importa as arenas no Poco X8 Pro, mas os dois botões superiores ficavam cobertos pela área de notificações; as arenas pareciam divididas em trechos isolados.

**Causa encontrada:** no Java, a toolbar não aplicava os insets do sistema no Android 15. No WebGL e no fallback Canvas, `onlySelected=true` mais `scene.focusSelected()` ao abrir a arena ocultavam os demais meshes, apesar de todos já serem importados.

**Alterações realizadas:** `MainActivity.java`: layout horizontal centralizado, botões com pesos iguais, altura 52dp e `WindowInsets` explícitos em API30+; `fitsSystemWindows` anterior. `web/scene3d.js`, `web/scene3d_fallback.js`: começam com `onlySelected=false`, controle `scene3d-show-all`, `getVisibleCount()`, enquadramento sem mudar visibilidade. `web/bundle_loader.js`: após montar recursos chama `focusAll()` e mostra contagem de malhas da arena. `tools/build_private_editor.py` gera tanto HTML pessoal quanto template Android sem recursos proprietários (`--android-template`). Template nativo atualizado, `android/app/build.gradle`: versionCode 2, versionName 0.2.0-alpha.

**Verificações executadas:** 9 testes Python e suíte JS de colisão passaram; novos asserts de composição passaram; HTML pessoal gerado a partir do XAPK privado apresentou 9 arenas e 75 malhas válidas. Playwright/Chromium headless mobile (430×875): CityA com 9 visíveis após abrir, selecionar Zone03 e focar; alternância para uma malha exibe 1; Ver arena restaura 9; CityB com 10; exportação de patch mantida; nenhum erro JS.

**Limitações:** mudança de insets na interface Java ainda depende de execução física no Poco para confirmar o toque no topo. "Montar tudo" é **visualização simultânea das malhas físicas nas coordenadas originais**, não conversão para uma única malha, nem edição dos prédios, água ou IA; as 12 malhas não validadas continuam ausentes. Compilação APK CI será registrada após resultado.

### Ajuste de assinatura no APK v0.2 (ChatGPT)

A análise dos blocos APK Signature Scheme v2 dos APKs debug v0.1 e v0.2 mostrou **certificados diferentes**: v0.1 SHA256 `208e3d76f48279b15612fdd8d4c5a4a96e5817000025c940b869e074f5362b06`; v0.2 anterior SHA256 `07f3b1f728bd4814e43060070be2c032f80b03bed9dd27bd4f1e6cc6dedf8d7d`. Por isso, instalar v0.2 como atualização seria rejeitado por assinatura incompatível. Solução para testes sem perda de dados: adicionar `applicationIdSuffix '.v02'` no `debug` e exibir o rótulo `Riptide Map Lab v0.2`. A versão v0.1 segue instalada. A importação original de XAPK é necessária uma vez na v0.2 porque os dados são privados por package ID. Para builds de produção futuras, configurar uma chave de assinatura persistente e protegida em GitHub Secrets (ainda não realizado).
