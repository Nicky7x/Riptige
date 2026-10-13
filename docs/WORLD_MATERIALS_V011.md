# v0.11 alpha — materiais com UV e vínculos de água por arena

## Implementação da integração 3D
O GLB privado agora é gerado por grupos de material usando `visual_models.py`, com os UVs dos layouts de vértice conhecidos (strides 20,24,28,32,36). Os nomes dos materiais são preservados em `glTF.materials[].name`. No Android, `world_scene.js` procura `VuMaterialAsset/<nome> → DiffuseTexture → VuTextureAsset` no catálogo privado que já é produzido por `ApfImporter`. Renderiza PNG difuso apenas quando UV, material, imagem e WebGL são compatíveis. A ausência de qualquer parte cai para cor simples, sem inventar textura.

O exportador `build_private_world_library.py` extrai o APF do XAPK uma única vez em cache temporário e processa as 9 arenas, gerando 9 GLBs e metadados aquáticos. A biblioteca ZIP é gerada e importada **somente no celular do usuário**. Execute no Termux com a branch `feature/materials-water-world-v011`, seguindo `docs/WORLD_LIBRARY_V010.md` e alterando a instrução `git clone --branch` para esta branch. O ZIP gerado anteriormente pela v0.10 NÃO tem UVs/materiais e precisa ser reconstruído.

## Água
O compositor aplica a matriz original de cada entidade `VuWaterSurfaceEntity`, `VuWaterRampEntity` ou `VuInfiniteOceanWaveEntity`. Registra o caminho original do `WaterMap` e verifica o cabeçalho dos recursos `VuWaterMapAsset` referenciados, com resolução e formato quando legíveis. O arquivo pessoal `water/<arena>.json` inclui `waterMaps` indexado por referência original.

**Limitação fundamental:** mesmo uma água com `WaterMap` conhecido não significa que sua topologia, mapa de deslocamento, amplitude das ondas, rampas e material estejam compreendidos. O editor **ainda apresenta uma superfície plana translúcida apenas onde X/Y Size foram decodificados**, e não reproduz fisicamente a água do jogo. Entidades com dimensões desconhecidas permanecem inventariadas, mas não são desenhadas. O inventário não é uma reconstrução integral da água.

## Ainda pendentes
- Decodificar formatos de textura que não são ETC1, DXT5, luminance ou RGBA, além de lightmaps, normal maps, environment maps, shaders e materiais especulares.
- Confirmar orientação UV, transparência e gama contra capturas das arenas reais.
- Entender a geometria real das superfícies de água, materiais e uso visual/espacial dos recursos VuWaterMapAsset.
- Reconstruir objetos animados, partículas, eventos, checkpoints e componentes desconhecidos.
- Validar a composição espacial e desempenho com as nove arenas do XAPK original **no Poco X8 Pro físico**.

## Testes
- `tests/test_material_world.py`: malha sintética, nome de material, UVs e GLB.
- `tests-js/world-v09.test.cjs`: glTF UV + nome de material, WebGL e API.
- GitHub Actions: Node, Python com numpy/trimesh, Gradle, JUnit, assembleDebug.
- O sucesso desses testes demonstra integração estrutural com dados sintéticos, não fidelidade total dos materiais ou uma pista executável no Renegade.

Não inclua XAPK, APF, GLB, ZIP ou JSON pessoal extraído do jogo no repositório público.
