# APF v6 — campos observados, não documentação oficial

**Fonte:** XAPK privado do usuário, inspecionado em leitura. Nenhum dado binário do jogo é disponibilizado.

| Posição em bytes | Tamanho | Interpretação |
|---:|---:|---|
| 0 | 4 | magic `FPUV` |
| 4 | 4 | versão = 6 (u32 little-endian) |
| 8 | 4 | offset do índice = 88909047 |
| 12 | 4 | contagem de recursos = 3294 |
| 16 | 4 | tamanho do índice = 200079 |
| 20 | 4 | valor desconhecido = 3612707118 (não assumir CRC) |
| 24–55 | 32 | `GooglePlay` mais preenchimento |
| 56–59 | 4 | desconhecido/reservado |

O índice termina no EOF: 88909047 + 200079 = 89109126.

## Entradas do índice

Formato observado: `nome UTF8 + NUL + struct <IIIII>`, onde os cinco u32 são **offset**, **tamanho descomprimido**, **tamanho armazenado**, **campo desconhecido**, **flags**. O nome `crc` usado em versões iniciais dos scripts é provisório. A semântica exata desse campo não foi confirmada.

Os 16 bits superiores de flags coincidem com `1=zlib` e `2=LZMA1 raw` nos recursos observados. Os 16 inferiores ainda não foram decodificados.

## Amostras descompactadas

- `Assets/AssetData`: zlib, 92265 bytes;
- `VuTemplateAsset/Levels/CityA`: LZMA1 raw, prefixo de propriedades `5d 00 00 00 04`, 1198119 bytes;
- `VuTemplateAsset/Levels/ParkA`: LZMA1 raw, 3057174 bytes;
- `VuWaterMapAsset/CityA/WS01`: LZMA1 raw, 8358 bytes;
- `VuCollisionMeshAsset/Level/CityA/Zone01_col`: LZMA1 raw, 79725 bytes.

Alguns fluxos LZMA1 não apresentam marcador EOS. O tamanho descomprimido deve ser conferido contra o índice; `eof=False` não implica automaticamente corrupção.

**Não demonstrado:** estrutura de entidades, geometria, formato editável, CRC/hash, round-trip, repacker, nem carregamento de pistas modificadas.
