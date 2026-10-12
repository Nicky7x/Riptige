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
