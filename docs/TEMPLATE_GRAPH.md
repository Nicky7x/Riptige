# Template de cena v6: decodificação estrutural (M1.16)

**Data:** 13/10/2026. **Escopo:** análise read-only de uma cópia original do XAPK disponibilizada pelo proprietário. Os dados binários, transformações exatas das cenas e texturas não foram publicados neste repositório.

## Resultado reproduzido

Conseguimos percorrer integralmente os nove recursos `VuTemplateAsset/Levels/<arena>` usando o parser `tools/parse_scene_graph.py`. O código recupera o grafo de entidades, nomes, tipos e propriedades, incluindo `VuTransformComponent`, `VuWaterSurfaceEntity`, `VuWaterRampEntity`, `VuInfiniteOceanWaveEntity` e referências a prefabs/modelos.

Os **33.187 registros de entidade** foram reconhecidos nas nove cenas de topo, sem hashes de propriedades não resolvidos nesse conjunto. Isso **não significa que 33.187 modelos 3D distintos tenham sido renderizados**, nem que as dependências de prefabs externos tenham sido expandidas. Nas nove cenas, há **151 entidades aquáticas**: 122 superfícies, 21 rampas e 8 entidades de ondas oceânicas. Dessas, 141 possuem referência explícita a um `VuWaterMapAsset`. Os mapas aquáticos não representam, sozinhos, a geometria posicionada da água.

Veja [resumo agregado por arena](scene-graph-summary.json). Os números são derivados de leitura local do arquivo original; o JSON público não contém coordenadas, modelos ou texturas proprietários.

## Estrutura do formato (comprovada nos nove templates)

As cenas começam com `<u32 1><u32 tamanhoTotal>`, seguidos de um valor recursivo tipado. Os valores reconhecidos são:

| Tag u32 | Significado observado | Payload |
| --- | --- | --- |
| `1` | Inteiro com sinal | `i32` (inclui coordenadas negativas inteiras) |
| `2` | Ponto flutuante | `f32` (podem existir sentinelas grandes) |
| `3` | Inteiro sem sinal | `u32` |
| `4` | Referência a string UTF-8 terminada em NUL | `i32` deslocamento relativo **ao início da tag** |
| `5` | Array | `u32` contagem, seguido por offsets `u32` relativos ao início do array |
| `6` | Objeto | `u32` contagem, depois registros `<u64 hashChave><u32 metadados><u32 offsetRelativo>` |

Os hashes das chaves são **FNV-1a de 64 bits**. Exemplos verificados: `X = 0xaf64154c86024d67`, `Y = 0xaf64144c86024bb4`, `Position = 0xc1611c0558728a2a`, `RootEntity = 0x7456288f86d4ad5a`. O parser recupera os nomes das chaves na tabela de strings presente no próprio recurso; não necessita de um dicionário fixo das propriedades.

**Importante:** strings tipo 4 *não* possuem comprimento na segunda palavra: a segunda palavra é o deslocamento **relativo à própria tag**. Confundir esse ponteiro com comprimento resulta em valores errados e impede a decodificação das cenas.

## Como usar sem modificar o jogo

```sh
python tools/parse_scene_graph.py ~/storage/downloads/SEU_JOGO.xapk --arena CityB --out /sdcard/Download/CityB-instancias-privadas.json
python tools/parse_scene_graph.py ~/storage/downloads/SEU_JOGO.xapk --out /sdcard/Download/Riptide-todas-instancias-privadas.json
python -m unittest discover -s tests -p 'test_parse_scene_graph.py' -v
```

`--out` exporta posições locais, rotações, escalas, referências a prefabs e propriedades aquáticas. **Não envie esse JSON para o repositório público**, pois ele contém metadados extraídos da sua cópia do jogo. Sem `--out`, o programa imprime apenas as contagens e o relatório de cobertura.

## O que ainda falta para reconstrução fiel dentro do app

1. **Compor transformações de pais e filhos** para obter posições mundiais; as coordenadas extraídas até aqui são **locais**. Validar unidades/ordem de Euler e escala, bem como transforms padrões omitidos.
2. Resolver as dependências de prefabs: um tipo `#Building/...` não é necessariamente um `VuStaticModelAsset` direto. Precisamos carregar a definição de prefab correspondente e seus componentes.
3. Desenhar água a partir das entidades originais, tamanhos, transforms, mapas aquáticos e materiais. Os valores comprovados permitem posicionar superfícies, mas o shader e comportamento de ondas da Vector Engine não foram reproduzidos.
4. Integrar o parser ao importador Android **sem comprometer o uso da v0.8**, mantendo assets originais somente no armazenamento privado do usuário.
5. Comparar imagens do editor e do Renegade sob câmeras equivalentes, antes de afirmar que as arenas estão completas.

**Estado atual:** decodificador estrutural e exportador privado funcionam; **não há APK novo nesta etapa**. O editor instalado ainda não posiciona/instancia automaticamente todos os objetos da cena com estes dados. Não alegar que já existe uma arena completa visualmente reproduzida.