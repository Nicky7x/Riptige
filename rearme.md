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


### Resultado final da v0.2 Android — GitHub Actions #14

- **Código efetivamente compilado:** commit `93a479683d4a70e154335a453ffe53c004a1b184` (inclui correção de sintaxe Gradle e aplicativo debug lado a lado), após editor 3D reunido no commit `b5d224d673a4e4f516838b9e5954c6ca7e196695`.
- **Primeira tentativa de build independente (#13):** falhou na avaliação do Gradle porque `debug { ... } release { ... }` estavam na mesma linha sem separador. Corrigido com blocos distintos em `android/app/build.gradle`.
- **Build final (#14):** [GitHub Actions](https://github.com/Nicky7x/Riptige/actions/runs/38310193000) completou com **success**; executou `:app:testDebugUnitTest :app:assembleDebug`, publicou o artefato `riptide-map-lab-android-debug` (ID 11774182623), APK **116.368 bytes**, SHA-256 `29831fe0cd4f7b0041147e930ad4162b93b60e0111b1176a88c02ed0e4671d4b`.
- **Compatibilidade de instalação:** pacote debug v0.2 é `com.nicky7x.riptidemaplab.v02`; a v0.1 permanece `com.nicky7x.riptidemaplab`. Podem coexistir e manter dados separados. Reimportação do XAPK apenas na primeira execução do novo pacote.
- **Ainda não comprovado:** instalação física da v0.2, insets da barra de status no Poco X8 Pro e desempenho da arena inteira com WebGL real. Interface de navegador/fallback foi validada com Playwright e malhas originais privadas; nenhuma arena modificada foi executada no jogo.


## 2026-10-12 — Android v0.2: botões acessíveis e arena unificada (ChatGPT)

**Motivação:** teste físico do Poco X8 Pro confirmou importação de arenas, mas botões "Importar XAPK" e "Abrir editor" ficavam encostados na barra de notificações; usuário pediu ver uma arena inteira, não nove malhas isoladas.

**Alterações:** `MainActivity.java` passou a respeitar uma área mínima superior de 64dp (além dos insets reais do sistema no Android 11+) e margem superior adicional no Android antigo, alinhando os controles num toolbar horizontal centralizado com botões mais altos. O template WebView recebeu o comando **Mover arena completa** e explicita que a visão 3D reúne **todas as malhas de colisão de cada arena**. `web/bundle_loader.js` percorre cada malha da arena escolhida, atualiza suas coordenadas preservando arquivos separados e agrega os patches no manifesto JSON. O renderizador `scene3d.js` já possuía `loadArena(records)` para mostrar todas as malhas juntas; esta interface torna essa visão explícita.

**Método:** transformação de cada recurso via `RiptideCore.parse`/`updateVertex`, comparação com base original e atualização de preview e estado persistente; saída de patch continua incluindo nome de recurso individual para não corromper relações APF. Não se juntam bytes binários dos colliders em um único recurso.

**Limites:** juntamos **visualmente** os trechos em uma mesma cena, não modelos texturizados, e ainda não há prova de que mudanças carregam no jogo. Validação final requer teste no Poco. O novo APK depende do sucesso de GitHub Actions.


## 2026-10-12 — M1.8: interpretação e prévia dos modelos 3D visuais (ChatGPT)

- **Pedido:** foco no desenvolvimento de recursos visuais; separar rigidamente os modos Arena inteira e Trecho individual.
- **Descoberta:** formato `VuStaticModelAsset/Level` tem três distâncias LOD, lista de materiais UTF-8, grupos de 48 bytes com stream/material/offset/triângulos/AABB, buffers de vértices intercalados e índices u16. As primeiras 12 bytes de cada vértice são XYZ f32. A ordem entre `stream_index` e `material_index` foi verificada cruzando a soma das contagens de índices de modelo grande.
- **Método:** parser Python read-only `tools/visual_models.py` com limite de recursos e comparação com dados reais, seguido de porta Java `ApfImporter.makeVisualPreview()`. São criados buffers sintéticos de prévia em formato compatível com o renderizador, sem reutilizar esses bytes para alterar o jogo.
- **Evidência:** 223 de 248 modelos sob `VuStaticModelAsset/Level/` passaram validação Python, 25 rejeitados por variantes não decodificadas ou tamanho divergente; `CityA/Zone01` contém quatro streams de vértices com strides distintos (32/28/24/28). O jogo original não foi alterado.
- **Integração Android:** importador local cria catálogo `__visuals` com modelos visuais embutidos no armazenamento privado; `web/bundle_loader.js` separa camadas visuais/físicas e vista arena/trecho. O modo visual é **somente leitura sem texturas**, enquanto modo colisão mantém as edições. A exportação de patch continua exclusiva das colisões.
- **Testes efetuados:** 12 testes Python, incluindo três sintéticos para modelos visuais; Chromium renderizou 20 modelos visuais de CityA na arena toda, quatro associados a um trecho, e comutou para colisões sem erros de JavaScript. Smoke inicial com um modelo CityA também passou.
- **Bugs CI observados e corrigidos:** inclusão do JSON `__visuals` exigia tratamento de `JSONException`, além de corrigir quebra de linha literal inserida no primeiro patch; execução final do Actions é a fonte de validação de build.
- **Limites:** não decodifica texturas/materiais instanciados, nem transforma os modelos visuais em recursos modificados carregáveis no jogo. Falta validação no Poco X8 Pro para importar os novos modelos e fluidez da cena.


## 2026-10-12 — M1.9: build Android visual v0.3 concluído

- **Build:** [GitHub Actions #38314935003](https://github.com/Nicky7x/Riptige/actions/runs/38314935003) **success**, incluindo testes unitários Android, `assembleDebug` e upload de artefato.
- **Arquivo confirmado:** `Riptide_Map_Lab_Android_v0.3_visual_debug.apk` (121288 bytes), SHA-256 `c0a5010ac58847847947ab238402a386cda849a1d3b072239bcdc693c35a87f4`. APK contém `classes.dex`, `AndroidManifest.xml` e `assets/editor_template.html`. Nenhum arquivo proprietário do jogo foi incluído.
- **Testes da interface:** Chromium com dados da própria amostra do usuário alternou entre física (cinco partes testadas) e visual (vinte modelos), exibindo um único trecho físico ou quatro modelos associados ao trecho escolhido, sem exceções JS.
- **Necessidade de migração:** o cache criado pela versão Android v0.2 não contém `__visuals`; o usuário deve tocar em **Importar XAPK** novamente uma vez após instalar v0.3 para construir o novo catálogo local.
- **Limites:** APK compilado mas ainda não testado fisicamente em Android; 3D visual sem texturas ou suporte de escrita no APF de modelos.


## 2026-10-12 — M1.10: v0.4, corrigir tela do editor em branco após reimportar (ChatGPT)

- **Relato do proprietário (Poco X8 Pro):** a v0.3 importava XAPK, mostrava cerca de 23 recursos ignorados e a mensagem "Editor 3D · arenas locais · sem upload", mas o WebView ficava sem a interface visível. A versão v0.2 importava e mostrava o editor normalmente.
- **Diagnóstico de código:** `MainActivity.showEditorIfReady()` montava uma string HTML única com **todo** o JSON de colisões + modelos visuais inline, e chamava `web.loadDataWithBaseURL`. O aumento da biblioteca visual após v0.3 pode ter ultrapassado limites práticos de memória/IPC/WebView. Ainda **não há logcat** do aparelho, portanto esta causa é plausível, não confirmada.
- **Correção estrutural:** carregar somente `editor_template.html` (~60 KB), injetando `{"__external_bundle":true}`, em vez do JSON completo. O Java serve `arenas_bundle.json` diretamente de armazenamento privado por `WebViewClient.shouldInterceptRequest` em `https://appassets.androidplatform.net/arenas_bundle.json`. Nenhum pedido externo é atendido; URLs desconhecidas recebem 403. O frontend `web/bundle_loader.js` usa `fetch('/arenas_bundle.json')` e inicia assíncronamente.
- **Diagnóstico:** adicionados `WebChromeClient.onConsoleMessage` e `AndroidBridge.reportError()` para exibir mensagens de erro na interface Android, em vez de permanecer indefinidamente na mensagem genérica. O frontend captura exceções de inicialização e mostra a causa na página.
- **Segurança:** arquivos do jogo e catálogo continuam somente no armazenamento do aplicativo; arquivos proprietários não foram publicados nem enviados para servidor remoto. Mantidas restrições de acesso a arquivos e navegação na WebView.
- **Teste pendente:** conferir compilação no GitHub Actions e validar o carregamento no Poco. Os ~23 recursos ignorados podem corresponder a variantes de modelos não suportadas e não caracterizam falha da importação por si só.


### v0.4 — resultado da compilação e teste da interface (continuação M1.10)

- **Build validada:** [GitHub Actions #38319862832](https://github.com/Nicky7x/Riptige/actions/runs/38319862832) compilou `:app:testDebugUnitTest :app:assembleDebug` e publicou o artefato.
- **APK:** `Riptide_Map_Lab_Android_v0.4_fix_debug.apk`, 123.152 bytes, SHA-256 `2e9556ee1bc23092ec1a9b6ff635367976d889bead058ba817aed77978e4b11d`. HTML embutido na APK tem ~60 KB com marcador `__EMBEDDED_ASSETS__`; o catálogo grande NÃO é mais concatenado na string HTML.
- **Smoke test independente:** Chromium headless abriu o `editor_template.html` extraído do APK e um catálogo JSON sintético servido por mock de `fetch()`; 1 arena/1 trecho carregaram, cena 3D apareceu e não houve erros JavaScript. **Não** é teste da interceptação nativa do Android nem do XAPK completo.
- **Problema adicional detectado:** cada `assembleDebug` do GitHub Actions usa um certificado de assinatura Android debug diferente (runners efêmeros). Os certificados v0.3 e v0.4 foram extraídos do APK e têm SHA-256 diferentes. Portanto, **instalação de atualização direta sobre v0.3 provavelmente será recusada**; para v0.4, desinstalar v0.3 e reimportar o XAPK original. Não apagar o XAPK original. Problema de consistência da assinatura deverá ser resolvido futuramente por uma chave de teste estável, preferencialmente configurada como segredo privado no Actions.


## 2026-10-12 — M1.11: v0.5 corrigir crash imediato após abrir v0.4 (ChatGPT)

- **Relato do usuário:** no Poco X8 Pro, v0.4 fecha assim que é aberta, antes da importação.
- **Causa encontrada por inspeção:** `MainActivity.buildLayout()` invoca `WebSettings.setBlockNetworkLoads(false)` sem que `AndroidManifest.xml` declare `android.permission.INTERNET`. Conforme documentação Android e implementação Chromium, isso lança **SecurityException ("application missing INTERNET permission")** imediatamente durante a criação da WebView. Esta é uma causa **determinística pelo código**; ainda não foi coletado logcat físico do usuário.
- **Alteração:** declarar `<uses-permission android:name="android.permission.INTERNET" />` no manifesto, mantendo `shouldInterceptRequest` para atender somente `/arenas_bundle.json` do armazenamento interno e devolver 403 para outros pedidos. Assim a interface pode carregar o catálogo local sem enviar arquivos à rede. A existência da permissão não implica upload.
- **Validação:** [GitHub Actions run #38320836381](https://github.com/Nicky7x/Riptige/actions/runs/38320836381) terminou **success** na compilação e testes de unidade e publicou `app-debug.apk`. APK: 123200 bytes, SHA-256 `d4e4e9f747cb04d778c924d90bf93c39e0643480c8d2b2138233e95e058234cd`. Conferido no manifesto binário que a permissão `android.permission.INTERNET` está presente; APK contém o HTML do editor e nenhum recurso original do jogo.
- **Risco restante:** ainda não houve teste no Poco com APK v0.5; pode haver um segundo bug de carregamento após a tela inicial. Se necessário, coletar `adb logcat -b crash -d -v time` ou relatório de bug somente com trechos de `FATAL EXCEPTION`, omitindo dados pessoais. Várias builds debug GitHub podem usar certificados diferentes; desinstalação da versão antiga pode ser necessária.


## 2026-10-12 — M1.12: vídeo revela HTTP 403 da página `data:` (v0.6)

- **Relato:** na v0.5, o usuário importou o XAPK mas o editor ficou na tela de erro; o aplicativo **não** gerou erro de crash no app de logcat usado.
- **Evidência visual direta:** gravação `Screenrecorder-2026-10-12-20-27-41-130.mp4` do Poco X8 Pro exibe WebView com texto `Página da Web não disponível`, endereço `data:text/html;charset=utf-8;base64,` e erro `net::ERR_HTTP_RESPONSE_CODE_FAILURE`. Em outro trecho da gravação, aplicativo de log apresenta `0 logs`. Portanto o erro é uma requisição de conteúdo HTML bloqueada, não necessariamente fechamento/crash de processo.
- **Causa localizada no código:** `MainActivity.WebViewClient.shouldInterceptRequest` devolvia HTTP **403 para TODAS as URLs**, exceto `https://appassets.androidplatform.net/arenas_bundle.json`, inclusive o documento `data:` produzido internamente por `WebView.loadDataWithBaseURL`. O Android WebView recebeu 403 ao tentar mostrar seu próprio documento HTML.
- **Correção:** esquemas internos `data:`, `about:`, `blob:` agora devolvem `null` no interceptor, delegando à WebView. `https://appassets.androidplatform.net/arenas_bundle.json` continua único endpoint servido com dados do armazenamento privado; URLs remotas continuam bloqueadas. Added `onReceivedError`, `onReceivedHttpError`, `onRenderProcessGone` com erros visíveis.
- **Teste de regressão:** `WebRequestPolicy.java` extrai a política pura e `WebRequestPolicyTest.java` testa explicitamente liberação de `data/about/blob` e bloqueio de origem/caminho divergentes. `MainActivity` usa o helper.
- **Versão:** metadata do Android `versionCode 6`, `versionName 0.6.0-alpha`, label v0.6. A etapa de build final no Actions e teste físico no Poco ainda devem ser checados antes de afirmar resolução.
- **Não** publicar o XAPK original, APF nem HTML com modelos do usuário.


## 2026-10-12 — M1.13: v0.7, cockpit horizontal + câmera de jogador (ChatGPT)

- **Pedido:** evolução visual da interface inspirada em uma engine mobile; paisagem/horizontal no Poco X8 Pro, cena ocupando a maior parte da tela, botões agrupados nas laterais e identificação de funções ao toque, joystick para primeira pessoa. Texturas ainda não entram neste marco.
- **Android:** `AndroidManifest.xml` define `android:screenOrientation="sensorLandscape"`; `MainActivity` agora esconde a toolbar nativa **após** o frontend sinalizar editor pronto, ativa modo fullscreen imersivo e permite reimportar XAPK por `AndroidBridge.pickXapk()` no painel de ferramentas. Durante a importação inicial, a toolbar e barra de status permanecem visíveis. Mantida a política offline da WebView, restrita a catálogo privado.
- **Renderizadores:** `web/scene3d.js` e fallback `web/scene3d_fallback.js` implementam `setPlayerMode(enabled)`, `setJoystick(x,y)` e orientação livre com arraste do dedo. Em jogador, movimento no plano XY, câmera a altura heurística em relação ao menor Z da geometria visível; sem física de corrida, colisão, gravidade ou caminho automático. FPS de atualização de movimento limitado pelo `requestAnimationFrame`, delta temporal limitado a 0,05s.
- **Interface:** `web/mobile_landscape.css` e `web/mobile_landscape.js` criam HUD de topo com arena e trecho, canvas central, controle lateral de navegação (orbitar/focar/mover/jogador), barra lateral direita (arena/trecho/visual/colisões/exportar/mais), legendas com nome e função a cada toque, joystick virtual com Pointer Events e painel avançado com os campos já existentes. `android/app/src/main/assets/editor_template.html` mantém os sete scripts offline integrados, sem rede.
- **Compatibilidade:** o modo visual continua **sem texturas** e somente leitura, as colisões continuam experimentais, não há pista reproduzida dentro do jogo. A v0.7 conserva a importação de XAPK v0.6 sem expor seus assets na build pública.
- **Validação da interface:** `/mnt/data/riptide-v07/test_mobile.py` gerou malhas sintéticas, abriu o HTML v0.7 em Chromium 932×420, conferiu viewport, selecionou `CityA`, ativou câmera de jogador e joystick, alternou de volta e passou para geometria visual, abriu ferramentas avançadas, sem `pageerror`. Screenshot `/mnt/data/riptide-v07/landscape_mock_preview.png` contém somente dados sintéticos. Os arquivos locais de teste não estão no GitHub.
- **CI:** `tests-js/mobile-v07.test.cjs` inspeciona scripts embutidos, API de câmera e orientação; `.github/workflows/build-android.yml` inclui validação Node antes de executar testes JUnit e compilar APK. Teste de script teve uma primeira falha devido a regex com escapamento incorreto e foi corrigido para scanner manual de tags.
- **Ainda pendente:** build final aprovada com verificação HUD + compilação e teste físico do APK no Poco. As texturas reais dependem de continuar a análise de materiais/UVs e de seus formatos de imagem.


### v0.7 — compilação e entrega (continuação M1.13)

- **Build final confirmado:** [GitHub Actions #38325819217](https://github.com/Nicky7x/Riptige/actions/runs/38325819217), status **success**, com validação Node dos scripts do HTML, testes de unidade Android e compilação `:app:assembleDebug` concluídas. O APK foi publicado como artefato `riptide-map-lab-android-debug` (ID 11780283411).
- **APK extraído e verificado:** `Riptide_Map_Lab_Android_v0.7_debug.apk` com 131.352 bytes, SHA-256 `029e677f463fd4101ea57a833bf58013113be42850f85d947820beaf9e521b76`. O APK contém HTML ~79 KB com CSS e JS do joystick embutidos, manifesto Android, dex e **não inclui assets comerciais**. Cópia entregue em Biblioteca `/RiptideMapLab/Riptide_Map_Lab_Android_v0.7_debug.apk`.
- **Smoke no Chromium:** 932×420 pixels, duas malhas sintéticas de CityA e uma de CityB; captura confirma botões nos dois lados, centro com cena real (sintética) em projeção, topo com arena, tooltip discreta; ativar perspectiva do jogador, tocar joystick, voltar para navegação órbita e alternar visual/colisão e abrir ferramentas não gerou pageerror. Prévia `/mnt/data/riptide-v07/landscape_mock_preview.png` no contexto desta execução.
- **Pendência:** instalar e testar a v0.7 fisicamente no Poco X8 Pro, especialmente comportamento da tela cheia pós-importação, toque multissensor do joystick e reimportação de XAPK no painel "Mais". Assinatura debug do runner GitHub pode exigir desinstalação da v0.6; exportar os patches antes de limpar dados.


## 2026-10-12/13 — M1.14: direção de gestos e prévia de texturas reais (ChatGPT)

**Relato do proprietário:** v0.7 opera normalmente no Poco, mas movimento horizontal de câmera e arraste vertical de estruturas parecem invertidos; solicitou todos os recursos visuais texturizados, cores e imagens dos cenários.

**Correção de toque:** `web/scene3d.js`, `web/scene3d_fallback.js` e scripts embutidos no Android invertem o sinal de `yaw` (órbita) e `playerYaw` (perspectiva de jogador) no arraste horizontal; invertem o parâmetro vertical de `moveTo/translate` usado para movimentar uma malha XY por arraste. **Ainda não testado no hardware após correção**, embora v0.7 tenha sido aprovada no Poco.

**Descobertas confirmadas no XAPK original, sem publicação dos recursos comerciais:**
- Inventário: 740 `VuTextureAsset`, 346 `VuMaterialAsset` e 248 `VuStaticModelAsset/Level`.
- Em uma sondagem read-only de materiais de 245 modelos que puderam ser percorridos, 176 nomes únicos de material e 86 texturas difusas distintas referenciadas.
- Exemplo de ligação: `VuStaticModelAsset/Level/CityA/Zone01` → material `Building/City/ComD_Solid_vc` → parâmetro `DiffuseTexture` referindo `Building/City/ComD_Solid` → `VuTextureAsset/Building/City/ComD_Solid`. Não confundir com textura normal ou máscara.
- Header de `VuTextureAsset`: dimensões em offsets 21/25, níveis mip em offset 29, formato OpenGL em offset 33, primeiro payload em offset 70. Confirmadas texturas ETC1 (`0x8D64`) e BC3/DXT5 (`0x83F3`), mais formatos LUMINANCE/RGBA nos recursos observados. Os mips não são integralmente reconstruídos, apenas o nível base.
- Coordenadas UV dos streams estáticos mapeadas em offsets de stride 20→12, 24→16, 28→16, 32→20, 36→24. Grupos material/stream convertidos em offsets globais de índice; cada grupo aponta para sua textura quando a decodificação funciona.

**Código criado:**
- `android/.../TexturePreview.java`: leitura conservativa de cabeçalho, PNG local ETC1 via Android e decodificador DXT5/BC3 puro, limites de tamanho e proteção contra formatos desconhecidos.
- `android/.../VisualPreviewMeta.java`: grupos de índices + materiais + UVs em bytes little-endian. Não edita visual real do motor.
- `android/.../ApfImporter.java`: carrega metadados `__materials`, `__textures` e `uvblob/uvsize/groups` em `__visuals` **no cache privado do app**, usando apenas recursos do XAPK do proprietário; imagens limitadas a 256px de prévia e no máximo 160 texturas.
- `web/scene3d.js`: novo shader difuso WebGL, seleção por grupos de material, GPU texture lazy-load com PNG local em data URI, alfa parcial, fallback para sombreamento simples.
- `web/bundle_loader.js`: entrega metadados UV/textura por modelo ao renderizador. Sincronizado no `android/app/src/main/assets/editor_template.html`.

**Validação concluída:** Python read-only sondou os recursos reais com material difuso e offsets de formato; Node `tests-js/mobile-v07.test.cjs` e `tests-js/texture-v08.test.cjs`, JUnit `TexturePreviewTest` e build Android foram aprovados no [run #38332343448](https://github.com/Nicky7x/Riptige/actions/runs/38332343448). Artefato `app-debug.apk` de **141160 bytes**, SHA-256 `76e91e249d50803a8aa7fa2a22c6e653b5f5713a3702dd6dc332cb1adfcdac9a`; foi salvo em Biblioteca `/RiptideMapLab/Riptide_Map_Lab_Android_v0.8_debug.apk`. Nada de assets originais foi enviado ao repositório.

**Limitações importantes:** o app não reproduz materiais completos (normal maps, máscaras, cubemaps, lightmaps, iluminação real, água, céu, shader específicos); modelos sem UV/material/texture aceitos continuam sem imagem. A prévia visual ainda é somente leitura e não há arena editada e carregada no jogo. Os testes CI não executaram o APK num emulador ou aparelho real; pedir ao usuário para **reimportar XAPK** e avaliar texturas em CityA e outros níveis; coletar screenshot/log de falhas.


## 2026-10-12/13 — M1.15: scene-coverage & water reference audit (ChatGPT)

**Prioridade explicitada pelo usuário:** não basta ver modelos isolados; deseja reproduzir dentro do editor as nove arenas **originais completas com todos os recursos**. Não simular água/posicionamento arbitrariamente.

**Descobertas do XAPK do proprietário (read-only):**
- Os `VuWaterMapAsset/<arena>/...` são mapas de dados de imagem; não definem por si só geometria aquática. No `VuTemplateAsset/Levels/<arena>` há referências `<arena>/WS...`, `<arena>/WR...`, `VuWaterSurfaceEntity`, `VuWaterRampEntity`, `VuInfiniteOceanWaveEntity` etc.
- Novo `tools/scene_dependencies.py` identifica as referências exatas dos 9 templates: **141 de 141 recursos aquáticos** aparecem nas cenas correspondentes. Inclui nomes com variantes `FactoryA/Zone1_WS01`, `OldCityA/WS01_v2`, `FactoryB/WPlat01`; não pressupor somente WS01/WR01.
- Cabeçalho `VuWaterMapAsset` é diferente de `VuTextureAsset` (largura/altura/formato em offsets 20/24/32, não 21/25/33). Após corrigir parsing, 141 mapas com formato reconhecido: **135 DXT1 (0x83f1)**, **6 ETC1 (0x8d64)**; nenhum rejeitado. Para arquivos grandes, leitura só dos primeiros 70 bytes após decomprimir, sem carregar os mapas completos.
- Referências diretas de recursos nas nove cenas: **409 nomes de `VuStaticModelAsset`** (por arena), **9 animados**, **28 cubemaps**, **21 lightmaps**, **31 texturas** e **6 materiais**. São nomes em cenas de topo, não número de instâncias; prefabs aninhados podem referenciar mais. O editor v0.8 não desenha todos esses objetos.
- O impedimento principal é ler o **grafo binário e transforms de instâncias** de `VuTemplateAsset`: as referências de água e modelos estão presentes, mas ainda não sabemos extrair com confiabilidade suas posições, orientações e dimensões originais.

**Código e testes:** `tools/scene_dependencies.py` suporta APF, APK e XAPK aninhado (`base.apk/assets/Assets.apf`), sem uploads nem retenção de arquivos temporários. `tests/test_scene_dependencies.py` tem 3 testes sintéticos incluindo arquivo XAPK aninhado. Os testes passaram localmente e via workflow [Validate Original Scene Index](https://github.com/Nicky7x/Riptige/actions/runs/38335433458) **success**. Executado contra o XAPK real: nove templates, 141/141 referências de água.

**Artefatos de metadados:** `docs/water-scene-audit.json` (resumo de cobertura por arena), `docs/SCENE_REBUILD.md` (critérios de aceite e próxima implementação). Uma cópia local com lista completa de nomes por arena foi gerada privadamente, sem recursos binários proprietários.

**Próxima etapa técnica:** parser read-only das entidades do `VuTemplateAsset` e validação de UM transform de modelo e UMA entidade de água com posicionamento original. Só depois carregar toda a cena, sky e sistemas avançados. **Não foi gerado novo APK**, pois ainda não há geometria aquática posicionada corretamente para integrar. Não declarar arena reconstruída.


## 2026-10-13 — M1.16: decodificador completo de grafo de cena tipado (ChatGPT)

**Meta do proprietário:** reproduzir arenas originais completas no editor, com água, objetos e posicionamento fiel; prioridade sobre ferramentas cosméticas.

### Descoberta de engenharia reversa

- Consegui decodificar recursivamente os nove recursos `VuTemplateAsset/Levels/*` do XAPK original. Os nomes das chaves são identificados por hashes **FNV-1a64** das strings na tabela interna do próprio template.
- Cabeçalho de arquivo `<u32 1><u32 comprimento total>` seguido de valor tipado. Tags verificadas: `1` inteiro com sinal, `2` float32, `3` inteiro sem sinal, `4` string UTF-8 em offset **relativo à própria tag** (não comprimento), `5` array de offsets relativos e `6` objeto de campos `<u64 hash><u32 metadado><u32 offset relativo>`.
- Exemplos de FNV-1a64: `RootEntity=0x7456288f86d4ad5a`, `Position=0xc1611c0558728a2a`, `X=0xaf64154c86024d67`, `Y=0xaf64144c86024bb4`. Campos nomeados como `data`, `ChildEntities`, `type`, `name`, `Components`, `VuTransformComponent`, `Properties`, `Position`, `Rotation` e `Scale` foram recuperados estruturalmente, sem sondagem cega de floats.
- Descoberta importante: valores grandes como `3.40282306e38` podem aparecer como sentinelas `float32`; não rejeitá-los por magnitude enquanto forem finitos. Coordenadas negativas inteiras aparecem como tag 1 `int32`, não como `uint32`.

### Verificação no XAPK original

- **9/9 cenas parseadas integralmente**, sem hashes de propriedades não reconhecidos; **33.187 entidades de cena** reconhecidas (isso não é quantidade de meshes distintas).
- **151 entidades de água**, separadas em **122 `VuWaterSurfaceEntity`**, **21 `VuWaterRampEntity`** e **8 `VuInfiniteOceanWaveEntity`**. **141** dessas entidades referenciam explicitamente mapas de água; as outras podem usar recursos globais ou não possuir campo `WaterMap`.
- CityB: **3.782 entidades**, **14 entidades aquáticas** e **13 referências aquáticas**, com valores `Position/Rotation/Scale` locais decodificados. A hierarquia entre pais e filhos ainda precisa ser composta em coordenadas de mundo para renderizar a cena fiel.
- Outras referências de modelo normalmente usam `#` como prefixo de *prefab alias*, não um modelo independente diretamente. O exportador distingue essas fontes no campo `model_reference_type`.
- Nenhuma coordenada original extraída nem recurso proprietário foi enviada ao repositório público. O relatório agregado sem posições está em `docs/scene-graph-summary.json`.

### Entrega e testes

- `tools/parse_scene_graph.py` (leitor de APF/APK/XAPK em modo leitura, com limites de tamanho, profundidade e número de nós) e `tests/test_parse_scene_graph.py` (5 testes sintéticos: hashes, ponteiros relativos, transform negativo, cabeçalho e tag inválida).
- `docs/TEMPLATE_GRAPH.md` registra o formato observado, instruções e limitações; código público não contém imagens, vértices nem dados da cópia do jogo.
- Verificação local completa e [CI GitHub Actions](https://github.com/Nicky7x/Riptige/actions/runs/38337038053) **success**.
- Arquivo privado de metadados extraídos das nove arenas (ZIP compactado, sem XAPK/APF) salvo na Biblioteca do proprietário em `/RiptideMapLab/Riptide_Original_Scene_Instances_Private.zip`, não enviado ao GitHub.
- **Não foi compilado um APK novo**, pois o renderizador Android v0.8 não interpreta ainda instâncias nem compõe matrizes parentais. Não confundir posições locais com posições finais, nem declarar água/cena completa.

### Próxima implementação

Portar um subconjunto comprovado do parser para o importador Android, com cache privado de instâncias; compor transforms ancestrais e validar convenções de ângulos e pivôs para CityB; relacionar prefab aliases a `VuStaticModelAsset` e às texturas já carregadas. Depois recuperar superfícies aquáticas com geometria e parâmetros originais, sem planos inferidos.
