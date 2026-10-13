# Prévia de texturas — v0.8 Alpha

**Somente análise de arquivos fornecidos localmente pelo proprietário. Nenhuma textura, modelo ou arquivo binário do jogo é hospedado neste repositório.**

## O que foi identificado

O formato `VuStaticModelAsset/Level/<arena>/<model>` contém grupos de triângulos que apontam para nomes de materiais `VuMaterialAsset/<nome>`. Esses materiais têm o parâmetro serializado `DiffuseTexture\0`, que referencia `VuTextureAsset/<textura>`.

No inventário original do XAPK, existem **740 `VuTextureAsset`**, **346 `VuMaterialAsset`** e **248 modelos estáticos de nível**. Em uma sondagem Python de 245 modelos de nível cuja estrutura de materiais pôde ser percorrida, foram identificados **176 nomes únicos de materiais** e **86 imagens difusas distintas** referenciadas pelos materiais que existem no arquivo; esses números são de exploração do XAPK, **não são a quantidade de modelos/texturas confirmadamente visíveis no aplicativo**. O importador Java aplica validações mais estritas e pode aceitar menos recursos.

Os recursos de textura analisados têm cabeçalho com dimensões nas posições 21/25, mip count na posição 29, formato OpenGL na posição 33 e blocos da imagem a partir do byte 70. **Apenas os formatos verificados abaixo** são convertidos para prévia:

| Código | Tipo | Renderização alfa |
|---|---|---|
| `0x8D64` | ETC1 RGB8 | Android `ETC1.decodeImage` → PNG |
| `0x83F3` | DXT5/BC3 RGBA | Decodificador de blocos RGBA → PNG |
| `0x1909` | GL_LUMINANCE | Prévia cinza → PNG |
| `0x1908` | GL_RGBA | Prévia RGBA → PNG |

O importador limita texturas a 1024×1024 na entrada e converte previews para no máximo 256px de lado. A versão inicial não garante orientação UV correta em todas as superfícies.

## Ligação UV/material → WebGL

Os grupos de modelos são representados como `{start,count,material}` (offset e contagem de índices de triângulos). Coordenadas UV são lidas de streams de vértices reconhecidos de stride 20/24/28/32/36 bytes, validadas e comprimidas com gzip no catálogo privado. O renderizador WebGL faz draw de cada grupo usando seu diffuse PNG, luz direcional simplificada e transparência alfa. Grupos sem textura ou com layout desconhecido recebem sombreamento básico.

A camada visual é **somente para inspeção**. Mover geometria física não muda os modelos/UVs/materiais do jogo. Nenhuma alteração visual é reconstruída no `Assets.apf`.

## O que **ainda não está incluído**

- Lightmaps verdadeiros, normal maps, máscaras, reflexos environment/cube, vertex colors completos.
- Efeitos de shader especiais, transparência ordenada, água/refração, céu e iluminação dinâmica idêntica ao Renegade.
- Texturas que usam outros formatos ou cuja referência `DiffuseTexture` não pôde ser extraída.
- Renderização texturizada no fallback Canvas sem WebGL.
- Editor para alterar imagens, materiais e UVs e salvar essas alterações de volta no jogo.

## Testes e validação

- Testes JUnit sintéticos `TexturePreviewTest` verificam cabeçalhos ETC1/DXT5, um bloco DXT5 vermelho, parsing `DiffuseTexture` e offsets UV usados.
- Teste Node `tests-js/texture-v08.test.cjs` verifica os contratos Java/WebGL/HTML e a sintaxe dos scripts embutidos.
- Compilar o APK e fazer testes unitários **não comprova** que as texturas reais estejam corretamente posicionadas; é necessário testar no Poco X8 Pro.
- Após instalar a v0.8, o proprietário precisa usar **Importar XAPK** novamente para reconstruir o cache privado contendo `__materials`, `__textures` e os UVs da geometria visual.

Próximas investigações: mapear vertex colors, entradas de parâmetros diffuse/mask, normal maps, lightmaps, posicionamento por `VuTemplateAsset` e texturas com formatos ainda desconhecidos.
