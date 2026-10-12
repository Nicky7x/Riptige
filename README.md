# Riptide Map Lab — editor de arenas Android (experimental)

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

## Criar uma cópia pessoal no Poco X8 Pro

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
# Requer uma cópia local do Assets.apf extraída pelo proprietário.
python tools/apply_arena_patch.py \
  --source "$HOME/Assets.apf" \
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
