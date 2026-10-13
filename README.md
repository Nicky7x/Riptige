# Riptide Map Lab — editor de arenas Android (experimental)
![Imagem do jogo](https://image.api.playstation.com/cdn/EP0786/CUSA04558_00/FREE_CONTENT5XN6qnbzXyLL9Qm4mJ2Q/PREVIEW_SCREENSHOT8_490657.jpg)

Projeto independente e não oficial de engenharia reversa de **Riptide GP: Renegade**. Objetivo: permitir criação de pistas personalizadas no Android, começando pela leitura, visualização e edição de **malhas de colisão** da Vector Engine.

**Situação em 12/10/2026:** a **edição de malhas e o round-trip de APF são experimentais e testados estruturalmente**; ainda **não** existe uma pista inédita carregada dentro do jogo, nem um APK modificado confirmado. O jogo é protegido por componentes PairIP e há campos de integridade desconhecidos.

## O que já funciona

- Índice de recursos APF `FPUV` v6 com **3.294 recursos** localizado e interpretado em modo leitura.
- **9 arenas** identificadas, com **75 malhas de colisão** que passaram pela validação estrita e podem ser pré-embutidas em um editor HTML pessoal.
- Editor gráfico para tela Android, **sem seleção manual de arquivos**, usando recursos embutidos gerados de uma cópia XAPK privada.
- Alternar arena/trecho, visualizar projeções de vértices e triângulos, mover vértices, deslocar malhas inteiras, desfazer/refazer, manter mudanças entre trechos e exportar um `riptide-arenas-patch.json`.
- Aplicar patches em uma **cópia** de `Assets.apf` com `tools/apply_arena_patch.py`. Em um teste com um vértice alterado de `CityA/Zone01_col`, o pacote reescrito preservou as **3.294 entradas** e passou na decodificação da malha modificada.

### Por que não colocar as pistas originais no GitHub?

O código-fonte do editor é público, mas os modelos/malhas/assets do jogo são conteúdo comercial. Por isso **nenhum APK, APF ou HTML com dados do jogo será colocado aqui**. O arquivo HTML *pessoal* com as arenas embutidas foi entregue privadamente ao usuário. Você também pode construir sua própria versão local sem fazer upload para site algum.

## Criar uma cópia pessoal no seu aparelho

No Termux:

```sh
pkg install python git -y
termux-setup-storage
git clone https://github.com/Nicky7x/Riptige.git
cd Riptige
python tools/build_private_editor.py \
  --source "$HOME/storage/downloads/SEU_ARQUIVO.xapk" \
  --out "$HOME/storage/downloads/RiptideMapLab-Pessoal.html"
```

Basta abrir o HTML produzido no Chrome Android. **Ele terá as arenas já embutidas e não pedirá importação de `.bin`**. Funciona também totalmente offline depois de gerado. O XAPK só é lido localmente para construir esse HTML; não é enviado à internet.

Para uma versão genérica *sem* assets, veja [`web/index.html`](web/index.html). A [versão pública no GitHub Pages](https://nicky7x.github.io/Riptige/) não embute recursos proprietários, então ela não substitui a versão pessoal.

## Editar e reconstruir um APF experimental

No editor pessoal: escolha a arena e o trecho, edite a malha e toque em **Exportar alterações de todas as arenas**. Um `riptide-arenas-patch.json` será baixado.

Para testar somente a estrutura do APF sem instalar nada:

```sh
# Usa diretamente a cópia XAPK original; não precisa extrair o APF manualmente.
python tools/apply_arena_patch.py \
  --source "$HOME/storage/downloads/SEU_ARQUIVO.xapk" \
  --patch "$HOME/storage/downloads/riptide-arenas-patch.json" \
  --out "$HOME/Assets.modified.experimental.apf"
```

Este repacker preserva todos os recursos não alterados e anexa os payloads modificados antes de gerar um novo índice. **AVISO:** o cabeçalho contém campos desconhecidos; PairIP pode impedir que uma versão modificada do jogo seja executada. O output é uma prova experimental de reempacotamento, **não** um arquivo pronto para instalar. Não substitua arquivos do jogo instalado nem interfira no multiplayer.

## Validação

- Script pessoal gerado com 9 arenas e 75 malhas, ~4,55 MB em HTML.
- Navegador Chromium executado sobre o HTML com `set_content`: a malha abriu, transformação em 276 vértices foi aplicada, alternância de arena manteve a edição, e o patch foi baixado; nenhum erro JavaScript.
- 9 testes Python e suíte JavaScript com fixtures sintéticas passaram.
- Repacker experimental testado no APF privado: 1 vértice de `CityA/Zone01_col` modificado, índice de 3294 recursos preservado e dados recomprimidos reextraídos com sucesso.
- **Nenhum** teste de carregamento in-game nem teste no Poco do usuário.

## Documentação e coordenação

- [`rearme.md`](rearme.md): diário obrigatório de alterações, métodos, testes e limitações.
- [`CLAUDE.md`](CLAUDE.md): instruções para outro agente.
- [`docs/FORMAT_APF_V6.md`](docs/FORMAT_APF_V6.md): campos conhecidos.
- [`docs/EDITOR_ANDROID.md`](docs/EDITOR_ANDROID.md): manual da versão genérica.
- [Issue de colaboração ChatGPT ↔ Claude](../../issues/1).

**Próximo marco para uma pista jogável:** decodificar serialização de modelos 3D, templates e vínculos de física/IA e encontrar forma autorizada de carregar recursos modificados, validando in-game.


## Editor 3D no Android — atualização de 12/10/2026

O **gerador pessoal** `tools/build_private_editor.py` agora produz um HTML único e offline com interface tridimensional para as malhas de colisão incorporadas. **Os assets não estão no GitHub.**

- Renderização 3D com WebGL1 e fallback Canvas 2D com projeção 3D (sem bibliotecas externas).
- Seleção de uma das 9 arenas e 75 malhas de colisão validadas, com abertura do trecho preferencial `Zone01_col`.
- Câmera orbital controlada por toque, zoom por gesto de pinça, panorama com dois dedos e botão para enquadrar trecho ou arena inteira.
- Selecionar malha tocando nela, alternar para **Mover trecho** e arrastar a geometria de colisão no plano horizontal (XY).
- Manter alterações ao mudar de trecho/arena e exportar `riptide-arenas-patch.json`.

### Gerar sua versão 3D pessoal

```bash
python tools/build_private_editor.py --source /sdcard/Download/SEU_JOGO.xapk --out /sdcard/Download/Riptide_Map_Lab_3D_Pessoal.html
```

Abra o HTML diretamente no navegador Android, sem instalar APK ou depender de servidor. Para usuários com navegadores sem WebGL, o programa muda para renderização 3D simplificada via Canvas automaticamente.

**Verificações:** o editor com 9 arenas foi aberto em Chromium headless em modo celular; em ambiente sem WebGL o fallback mostrou a malha real; órbita, seleção, alternância de arenas e exportação de mudanças em **951 vértices** foram exercitadas sem erros JS. **Não é teste feito no Poco físico** nem demonstra carregamento da pista no jogo.

**Escopo e limitação:** o visor 3D exibe exclusivamente malhas de colisão originais, não geometria visual/texturizada. Deslocamentos XY têm efeito apenas na cópia binária editada; o APF experimental permanece separado. Adicionar modelos, rampas visuais, água, checkpoints ou IA exige decodificação adicional.


## Aplicativo Android nativo (Java + editor 3D integrado) — alfa

Novo projeto em [`android/`](android) com workflow de [build do APK](.github/workflows/build-android.yml). O app oferece **importação única, local e offline** do XAPK original pelo seletor Android, lê `assets/Assets.apf`, valida/decomprime malhas compatíveis (APF v6, zlib e LZMA1), guarda os recursos apenas no armazenamento privado do aparelho, mostra o editor 3D e exporta patches via diálogo do Android. Não inclui os arquivos comerciais do jogo no repositório.

- [Como usar / compilar](README-ANDROID.md)
- [GitHub Actions: builds e artefatos](../../actions/workflows/build-android.yml)
- O app usa Java + WebView acelerado para manter a interface 3D já desenvolvida, evitando refazer a renderização em Kotlin puro.
- **Status de distribuição:** a compilação remota precisa resultar em sucesso para que haja um `app-debug.apk` disponível. A compilação inicial falhou por ação de SDK obsoleta; workflow corrigido para `android-actions/setup-android@v4` e nova compilação iniciada.
- O que se edita são malhas de colisão, **não** os modelos visuais ou uma arena pronta para executar no Renegade.


### Primeira build Android aprovada — 12/10/2026

**GitHub Actions [run #11](https://github.com/Nicky7x/Riptige/actions/runs/38308033274)**: **success** em `:app:testDebugUnitTest :app:assembleDebug`. Artefato `riptide-map-lab-android-debug` (ID 11773641104) gerou `app-debug.apk` de **115.296 bytes** (SHA-256 `03e2f5bd179acf203c31cb22a4b2fc78689ec06d0011d9033db6694bff5e43e9`). Esta é uma build **debug** compilada em runner GitHub, não um APK de publicação na Play Store.

**Importante:** falta teste de instalação, importação real do XAPK e performance WebGL no Poco X8 Pro. O APK NÃO contém arquivos proprietários do jogo. Ao iniciar, selecione sua cópia original do XAPK apenas uma vez, para extrair recursos localmente. Nenhum jogo instalado é modificado.


## v0.2.0-alpha — ajustes de usabilidade do Poco (12/10/2026)

- **Botões superiores** Importar XAPK e Abrir editor agora ficam centralizados, com margens e altura adequada para toque, e respeitam explicitamente os *WindowInsets* das barras de status e navegação (inclusive Android 15/targetSdk 35).
- **Arena inteira montada por padrão:** quando você seleciona uma arena, todas as malhas de colisão reconhecidas aparecem juntas em suas posições originais na cena 3D. Exemplo do XAPK testado: CityA possui 9 malhas compatíveis; CityB possui 10. O número varia entre arenas.
- **Focar seleção** apenas aproxima a câmera, sem esconder o restante. Marque/desmarque **Arena completa (todas as malhas)** para alternar entre vista completa e uma malha isolada; **Ver arena** volta à vista completa.
- O editor **não funde nem altera os arquivos binários originais** na visualização. Eles permanecem separados para que cada patch corresponda ao recurso APF correto. Ainda só mostramos geometria de colisão, não os modelos texturizados ou uma arena jogável.
- [Notas de versão e testes](docs/RELEASE_NOTES_v0.2.md).

Para atualizar, baixe o artefato da build Android v0.2 em [GitHub Actions](../../actions/workflows/build-android.yml) quando ela estiver concluída. **Não desinstale a v0.1:** a versão debug v0.2 usa identificador próprio para instalar lado a lado. Importe o XAPK novamente uma vez na v0.2.

**Instalação da v0.2 ao lado da v0.1:** os APKs debug do Actions são assinados com certificados diferentes; a versão v0.2 usa temporariamente o identificador `com.nicky7x.riptidemaplab.v02` para instalar como aplicativo separado. Isso evita desinstalar a v0.1 e perder dados. Na v0.2 será necessário importar sua cópia XAPK mais uma vez. O nome exibido será **Riptide Map Lab v0.2**.


## Fase visual — v0.3 alfa (12/10/2026)

A leitura de `VuStaticModelAsset/Level` avançou: **223/248 modelos de nível** foram interpretados na análise local do XAPK original e podem gerar malhas sintéticas de visualização (XYZ + triângulos) **sem redistribuir os assets**. Consulte [docs/VISUAL_MODELS.md](docs/VISUAL_MODELS.md).

No aplicativo, após importar novamente o XAPK original, escolha entre **Geometria visual 3D** (somente leitura, sem materiais ou texturas) e **Colisões (edição)**. As duas vistas são separadas. Há dois modos mutuamente exclusivos: **Arena inteira** ou **Trecho individual**. O modo visual não tem escrita/injeção de modelos no jogo. Atenção: arenas importadas em versões anteriores não têm o catálogo visual; **é preciso reimportar o XAPK uma vez** após atualizar.

Tests: 12 Python sintéticos aprovados, interpretação de 223 modelos reais (25 rejeitados com segurança) e Chromium exibindo 20 modelos de `CityA` em vista global e 4 associados ao trecho selecionado sem erros de JavaScript. O build Android e teste no Poco devem ser considerados etapas independentes.


### APK Android v0.3 — primeira prévia visual 3D

A build foi aprovada no [GitHub Actions](https://github.com/Nicky7x/Riptige/actions/runs/38314935003). A edição das colisões e a nova prévia dos modelos 3D originais ficam em camadas separadas. **É necessário importar novamente o XAPK original** após a atualização, porque o cache antigo não continha modelos visuais. Ver [formato validado](docs/VISUAL_MODELS.md).

O APK é **debug**, não está na Play Store e sua prévia visual não tem texturas nem escreve os modelos no APF. Ainda depende de teste prático em Android para comprovar performance e correta importação visual.


### Android v0.7 — landscape e câmera de jogador

A interface Android passou a ser horizontal (**sensorLandscape**) com HUD lateral e preview 3D ocupando o centro. Ela tem botões de câmera (orbitar, focar, mover e jogador), camada (visual/colisão), escopo (arena/trecho), exportação de patches e painel avançado. Cada ferramenta exibe o próprio nome e explicação ao toque. **Joystick virtual** no canto esquerdo permite movimentar uma câmera livre em primeira pessoa, e arrastar no canvas olha ao redor.

O modo jogador é **apenas de inspeção visual**: não simula física de jetski, contato com água, colisões nem percurso real. A camada de modelos visuais continua **sem texturas e somente leitura**. Para manipular colisões, volte ao modo órbita/colisão.

Na primeira importação, os botões nativos aparecem; após carregar o editor, o Android entra em fullscreen, mas **Importar outro XAPK** continua acessível em **Mais → Ferramentas avançadas**. Biblioteca local continua privada e offline.

Código: `web/mobile_landscape.js`, `web/mobile_landscape.css`, `web/scene3d.js`, `web/scene3d_fallback.js`, `android/app/src/main/assets/editor_template.html`. A validação de scripts e recursos mínimos está em `tests-js/mobile-v07.test.cjs`.

A compilação de APK pelo [GitHub Actions](https://github.com/Nicky7x/Riptige/actions/workflows/build-android.yml) precisa passar antes de usar um novo APK. O teste automatizado do HUD em Chromium usou apenas dados sintéticos e **não** substitui o teste de gestos e GPU no Poco X8 Pro. Se o Android não permitir atualizar um APK debug anterior por assinatura diferente, exporte qualquer patch e reinstale, pois a desinstalação apaga o cache privado.


## Android v0.8 — cores e texturas difusas originais (experimental)

A primeira versão texturizada do visualizador usa dados **extraídos somente do XAPK escolhido pelo usuário**, sem incluir imagens comerciais no código ou APK público. O importador identifica materiais `VuMaterialAsset`, suas referências `DiffuseTexture`, os arquivos `VuTextureAsset`, coordenadas UV dos modelos estáticos e grupos de triângulos por material. Converte localmente texturas ETC1 e DXT5 (e alguns formatos não comprimidos) para PNGs de prévia e desenha cada grupo usando sua imagem verdadeira quando disponível.

O visualizador WebGL usa sombreamento simplificado e alfa; **não** reproduz ainda normal maps, lightmaps, reflexos, shaders especializados, água nem 100% das texturas. Quando não há suporte ao recurso, mantém a geometria sem imagem. A camada visual continua apenas para inspeção, sem edição de modelos dentro do jogo. No fallback Canvas, as imagens não são desenhadas.

**Corrigidos também:** o sinal do arraste horizontal da câmera e o arraste vertical de objetos na visualização física (WebGL e Canvas).

**Importante:** após instalar v0.8, use **Importar XAPK** novamente uma vez para atualizar o catálogo privado; sem isso, o cache antigo não contém os UVs nem as texturas. As texturas nunca são enviadas a um servidor.

[Detalhes técnicos e formatos suportados](docs/TEXTURES.md).

**Validação:** [GitHub Actions #38332343448](https://github.com/Nicky7x/Riptige/actions/runs/38332343448) passou verificações Node, JUnit e `assembleDebug`; gerou `app-debug.apk` de 141160 bytes, SHA-256 `76e91e249d50803a8aa7fa2a22c6e653b5f5713a3702dd6dc332cb1adfcdac9a`. A correção de interação e a aplicação de texturas ainda precisam ser avaliadas no Poco X8 Pro.


### Novo avanço M1.16 — hierarquia original de cenas decodificada

Agora existe um [leitor dos templates originais](tools/parse_scene_graph.py), capaz de identificar o grafo de entidades, `VuTransformComponent` e as propriedades de água diretamente do XAPK do usuário. Foram verificadas as **9 arenas**, totalizando **33.187 entidades**, inclusive **151 entidades aquáticas** (141 com mapas aquáticos explícitos). O formato usa nomes de propriedades identificados por **FNV-1a64** e variantes tipadas; [detalhes e limitações](docs/TEMPLATE_GRAPH.md).

```sh
python tools/parse_scene_graph.py SEU_JOGO.xapk --arena CityB --out cityb-instancias-privadas.json
```

O JSON com coordenadas originais deve permanecer privado. **Ainda não compomos todas as transformações hierárquicas nem renderizamos as superfícies aquáticas completas no Android**; portanto a v0.8 instalada continua sendo o editor mais recente. Testes sintéticos e verificação [CI](https://github.com/Nicky7x/Riptige/actions/runs/38337038053) aprovados.


### Marco M1.18 — modelos do cenário posicionados com hierarquia original

[Compositor matemático de instâncias](tools/resolve_world_instances.py) percorre as nove arenas, aplica transforms de entidades/prefabs e produz coordenadas de mundo a partir da cena original, sem incluir assets comerciais no GitHub. **14.487 referências estáticas posicionadas** (contagem de instâncias expandidas), com **4.560 overrides de propriedades** aplicados. A ordem Euler ainda é hipótese; 32 overrides nas outras arenas não foram associados a filhos.

O [exportador de prévia pessoal GLB](tools/export_world_glb.py) já gerou **2.658 instâncias de modelos estáticos originais na CityB**, de 2.818 referências totais; 87 modelos distintos decodificados e 160 instâncias ainda não suportadas. O GLB e os JSONs com dados originais foram entregues **apenas na Biblioteca pessoal do proprietário**, não no repositório. É uma prévia 3D offline SEM texturas/água/efeitos do jogo. [Documentação e testes](docs/WORLD_TRANSFORMS.md).

```sh
python tools/resolve_world_instances.py game.xapk --arena CityB --out cityb-world-private.json
pip install numpy trimesh
python tools/export_world_glb.py game.xapk --arena CityB --output cityb-private.glb
```

**Status Android:** o app v0.8 instalado não recebeu ainda o leitor de hierarquias. Precisamos validar matrizes/pivôs e otimizar instâncias antes de inserir tudo na WebView Android; nenhum APK novo foi apresentado neste marco.


### Visão do produto — arenas editáveis e criação por IA

**Objetivo principal:** reconstruir fielmente as arenas originais como **cenas 3D integrais no editor**, de modo que o proprietário possa modificá-las e também solicitar que IAs gerem arenas inéditas. O editor **não pretende reproduzir a física nem a jogabilidade do Renegade**.

O roadmap deve priorizar: (1) importação e reconstrução espacial dos assets originais — modelos, prefabs, água, materiais e hierarquias; (2) seleção e manipulação de entidades, criação/remoção de objetos, geometria e salvamento; (3) **formato de cena documentado e versionado**, utilizável por agentes de IA para carregar, transformar e criar arenas de forma declarativa; (4) exportação de patches e, como esforço independente, eventual compatibilidade com o jogo. Renderização dos efeitos sofisticados é secundária quando não comprometer a visualização e edição correta do cenário.

O formato gerado por IA deverá representar entidades com IDs estáveis, transformações, hierarquia, referências a recursos, propriedades de água, layers e operações de edição. Os arquivos comerciais permanecem locais/privados; nenhum asset original deve ser versionado no repositório público.

**Estado atual:** a infraestrutura de interpretação de cenas/prefabs e uma prévia GLB privada de CityB existem, mas a reconstrução integral ainda **não foi integrada ao APK Android**. Ver [transformações](docs/WORLD_TRANSFORMS.md).


### Android v0.9 — modo de instâncias, primeiro ciclo de edição por IA

Além dos recursos da v0.8, a v0.9 abre **cenas GLB privadas** no próprio app: **Mais → Abrir cena 3D (GLB)**. A prévia pessoal de `CityB` contém **2.658 instâncias** reconstruídas por transforms originais e caminhos dos objetos. O visualizador WebGL1 compartilha buffers de modelos e utiliza `ANGLE_instanced_arrays` quando disponível. Inclui busca por nome/caminho, seleção, editar X/Y ↑/Z, duplicar/ocultar e **Cena JSON / Importar JSON** para colaborar com IAs.

A especificação [`riptide-world-edit-v1`](docs/AI_SCENE_V09.md) permite que uma IA altere o JSON exportado e insira novas instâncias de **meshes já existentes no GLB**. Ainda não suporta modelos criados do zero por JSON; também não reconstrói a arena dentro do jogo. O GLB é uma prévia de geometria **sem texturas ou água**; a visualização texturizada da v0.8 permanece disponível separadamente. Para usar este modo, é necessário selecionar o GLB pessoal; importação automática de cena/prefabs diretamente do XAPK no Android permanece em desenvolvimento.

[Validação automática do editor](https://github.com/Nicky7x/Riptige/actions/workflows/build-android.yml) executa teste de GLB e JSON, regressões da v0.7/v0.8, JUnit e montagem APK. Renderização, gestos e desempenho de GPU devem ser confirmados no Poco.


### v0.10 experimental — biblioteca 3D privada para TODAS as arenas

A v0.9 exigia selecionar manualmente um GLB e só havia uma prévia CityB disponível. A branch experimental v0.10 acrescenta um **gerador local de ZIP privado com GLBs das nove arenas e os respectivos metadados aquáticos**: `tools/build_private_world_library.py`. O app Android importa esse único ZIP e depois carrega automaticamente o GLB correspondente quando você troca a arena, dentro do viewport do editor. Nenhum GLB comercial entra no APK público.

A prévia aquática usa somente posições e tamanhos reconhecidos, como **planos diagnósticos**; não recria as ondas/mapas reais. Os GLBs **ainda não exibem as texturas da v0.8**, e diversos objetos/efeitos faltam. Ainda não há integração direta desse compositor ao importador XAPK Android; gerar o ZIP no próprio Poco via Termux é um passo separado, executado uma só vez. [Instruções e limites](docs/WORLD_LIBRARY_V010.md).

Status: **código experimental não validado no Poco e não equivale a pista jogável**.
