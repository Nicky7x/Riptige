# Modelos 3D estáticos — primeiras estruturas decodificadas

**12/10/2026 · Riptide GP: Renegade · análise própria de cópia XAPK disponibilizada pelo usuário.**

## Descoberta reproduzível

Os recursos `VuStaticModelAsset/Level/<arena>/<modelo>` têm uma estrutura que se mostrou consistente em **223 de 248 arquivos de modelo de nível**. A análise é somente leitura e produz **geometria de prévia**, não dados capazes de substituir uma cena dentro do jogo.

A estrutura observada contém:

1. Três `float32` de distância LOD no início e bounding box de nível.
2. `u32` contagem de materiais seguido por caminhos UTF-8 terminados em NUL.
3. `u32` contagem de grupos, cada grupo ocupando **48 bytes**: índice de stream, índice de material, offset inicial de índice, número de triângulos e AABB com 8 `float32` (inclui dois campos W não identificados).
4. Cabeçalho de streams `[u32 0, u32 streamCount]`.
5. Para cada stream: `u32 stride`, `u32 payloadLength`, buffer de vértices intercalados (as primeiras 12 bytes de cada vértice são XYZ f32), `u32 indexCount`, índices `u16`.
6. Um byte terminador `00` nos modelos reconhecidos.

O índice de material e o índice de stream são campos distintos: **não podem ser intercambiados**. A soma dos índices de streams coincide com os triângulos enumerados pelos grupos dos modelos verificados.

### Validação contra XAPK original

`VuStaticModelAsset/Level/CityA/Zone01` contém **4 streams de vértices**. Foram conferidos strides de 32, 28, 24 e 28 bytes, e índices que referenciam vértices existentes. O pequeno modelo `VuStaticModelAsset/AR/RampArrows` tem 18 vértices XYZ+UV com stride de 20 bytes e 12 triângulos.

O parser `tools/visual_models.py` e o leitor Java `ApfImporter.makeVisualPreview()` adotam validações conservadoras. **223 de 248 modelos** do prefixo `VuStaticModelAsset/Level/` passaram na análise Python; **25 foram rejeitados** por divergências de descompressão ou variantes ainda não interpretadas (incluindo modelos com dados adicionais). Não tratar recusas como modelos inexistentes.

As prévias criadas pelo Java são sintéticas, em formato `u32 vertexCount; N*4 float32 XYZW; u32 indexCount; M*u16 índices`, para reutilizar o renderizador WebGL existente. **Não são colisores válidos do jogo** e não podem ser reinseridas no APF como substitutas dos modelos visuais.

## Android / UX

A importação local de XAPK do aplicativo agora armazena, além das colisões, um bloco `__visuals` com modelos interpretáveis de cada arena. O editor permite **Geometria visual 3D** (prévia SEM texturas, apenas leitura) ou **Colisões** (editor atual). Os modos **Arena inteira** e **Trecho individual** são mutuamente exclusivos para a cena 3D. A seleção de trecho tenta correlacionar `Zone01_col` a modelos `Zone01`, `Zone01_ref` etc., porém não afirma correlação total de entidades.

## Testes e limitações

- **12 testes Python sintéticos** passaram; parser real de 223 modelos foi exercitado fora do Android; smoke test Chromium sobre dados reais de `CityA/Zone01` navegou entre as quatro combinações de vista sem erros JS.
- Os modelos **não têm materiais nem texturas renderizadas** nesta versão, e podem ter transforms de instância que ainda não mapeamos.
- Ainda não são modelos que o usuário possa mover e gravar no jogo; o botão de mover 3D é desativado na camada visual.
- O teste do APK compilado e o teste físico no Poco X8 Pro são validações distintas e precisam ser feitos separadamente.
