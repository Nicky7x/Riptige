# Diário de pesquisa reproduzível

## 2026-10-12 — Pesquisa inicial (ChatGPT)

**Questão:** quais arquivos armazenam pistas e objetos?

**Método:** inspecionar XAPK original de 124806805 bytes (SHA-256 `9e0ff1d409a76d25faf90bf920cdb734e297f6f0ef7dd7522e9991f954b18693`), encontrar `base.apk` (104662762 bytes) e `assets/Assets.apf` (89109126 bytes), validar índice FPUV v6 e descompactar cinco exemplos em modo leitura.

**Observado:** 3294 entradas, índice em offset 88909047 (200079 bytes), nomes de níveis CityA/CityB/FactoryA/FactoryB/MilitaryA/OldCityA/ParkA/ParkB/SpaceportA. Strings de alguns templates contêm `VuAiWaypointEntity`, `CheckPoint Width` e `Spline`.

**Falha relevante:** tentativa de decodificar um LZMA do APF como arquivo `.xz`/`.lzma` padrão; esses recursos usam LZMA1 raw com prefixo de 5 bytes, alguns sem EOF marcado.

**Testes:** quatro fixtures sintéticas de APF passaram localmente. Ainda não existe repack nem edição comprovada.

## 2026-10-12 — Comparação do extrator do Claude (ChatGPT)

**Procedimento:** `riptide_apf_extractor.py load()` versus leitor independente `parse_apf_index()`, sobre o mesmo APF; bytes extraídos versus `decompress_payload()`.

**Resultado:** nomes/offsets/tamanhos de todos os 3294 itens iguais. Saídas byte-idênticas nos cinco recursos: AssetData (92265 B), CityA template (1198119 B), ParkA template (3057174 B), CityA water map (8358 B), CityA collision mesh (79725 B).

**Pontos a corrigir no script do Claude:** memória (~89 MB), validação de limites, verificação do tamanho final, caminhos de saída potencialmente malformados; evitar usar na extração de APF não confiável. A existência de um campo chamado `crc` não demonstra algoritmo CRC.

## Próximo experimento

Investigar formato de `VuTemplateAsset` de forma read-only comparando `CityA`, `ParkA` e `FactoryA`. Entregar tabela de offsets, hipótese testável e testes sintéticos, sem incluir recursos proprietários no Git.
