# Riptide GP: Renegade — Map Lab

Laboratório comunitário **não oficial** para pesquisar o formato de pistas de *Riptide GP: Renegade* (Vector Unit), com foco em ferramentas Python que possam rodar no Termux/Android.

> **Estado atual:** leitura do índice APF v6, listagem de recursos e descompactação em modo somente leitura. **Ainda não existe mapa novo, editor ou repacker funcional.**

## Fonte e descobertas verificadas

Analisamos localmente a cópia do XAPK fornecida pelo proprietário. **O arquivo do jogo NÃO é publicado neste repositório.**

- SHA-256 do XAPK analisado: `9e0ff1d409a76d25faf90bf920cdb734e297f6f0ef7dd7522e9991f954b18693`
- Pacote: 124.806.805 bytes, `base.apk` e cinco APKs complementares.
- `assets/Assets.apf` dentro de `base.apk`: 89.109.126 bytes.
- APF com magic `FPUV`, versão `6`, índice na posição `88909047`, 3.294 recursos.
- Identificados nomes de ambientes: `CityA`, `CityB`, `FactoryA`, `FactoryB`, `MilitaryA`, `OldCityA`, `ParkA`, `ParkB`, `SpaceportA`.
- Amostras de recursos foram decodificadas via zlib ou LZMA1 raw. Strings como `VuAiWaypointEntity`, `CheckPoint Width` e `Spline` aparecem nos dados.

Isso **não prova** que seja possível criar mapas sem descobrir os formatos de cenas, colisões, água e referências internas.

## Arquivos

- [`rearme.md`](rearme.md): diário de toda alteração, motivação, procedimento, resultado e limites.
- [`CLAUDE.md`](CLAUDE.md): handoff obrigatório ao Claude e tarefas com critérios de prova.
- [`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md): evidências técnicas e erros.
- [`docs/FORMAT_APF_V6.md`](docs/FORMAT_APF_V6.md): descrição parcial do índice.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): prioridades até uma pista nova.
- [`tools/riptide_apf_extractor.py`](tools/riptide_apf_extractor.py): script inicial contribuído pelo Claude (revisão pendente de robustez).
- [`tools/inspect_xapk.py`](tools/inspect_xapk.py): inspetor incremental e validação somente leitura.
- [`tests/test_apf.py`](tests/test_apf.py): testes sintéticos sem recursos do jogo.
- [Issues](../../issues): canal de comunicação assíncrona entre agentes.

## Uso local no Termux

```bash
pkg install python -y
python -m unittest discover -s tests -v
python tools/inspect_xapk.py --xapk /caminho/privado/arquivo.xapk --out analysis/report.json
```

Todos os utilitários são para análise de uma cópia legitimamente obtida. **Não envie APK, XAPK, APF, modelos, texturas ou dados extraídos ao repositório.**

## Próxima meta

Interpretar a estrutura interna de `VuTemplateAsset/Levels/CityA`, comparando com `ParkA` e `FactoryA`, **sem modificar o original**. Exigir evidência por offsets e testes antes de construir qualquer ferramenta de escrita.

## Diário resumido

- **2026-10-12, início:** leitura de APF v6 e cinco recursos de amostra (somente leitura); quatro testes sintéticos passaram localmente.
- **2026-10-12, sincronização:** repositório iniciado, contribuições revisáveis de dois agentes e protocolo de colaboração em `CLAUDE.md`/`rearme.md`. Ver detalhes nos diários.

**Importante:** este projeto não é afiliado à Vector Unit. Sem redistribuição do jogo comercial nem interferência em multiplayer/anticheat.
