# Handoff — Claude e ChatGPT: Riptide Map Lab

Projeto de pesquisa **não oficial** para criar pistas novas em Riptide GP: Renegade, com execução no Termux/Poco X8 Pro e ferramentas Python.

## O que já foi confirmado no arquivo original (fora do GitHub)
- `base.apk/assets/Assets.apf` tem assinatura `FPUV`, versão 6, **3.294 recursos**; o índice começa em 88909047, tem 200079 bytes e termina no EOF.
- A lista contém `VuTemplateAsset/Levels/CityA`, `Levels/ParkA`, `VuWaterMapAsset/CityA/WS01` e `VuCollisionMeshAsset/Level/CityA/Zone01_col`.
- Alguns conteúdos são zlib; outros são LZMA1 raw com prefixo de 5 bytes de propriedades.
- ChatGPT comparou o extrator enviado pelo Claude com seu próprio leitor: os **3.294 nomes/offsets/tamanhos coincidem**; cinco recursos testados produziram bytes idênticos. Isso valida parte da extração, **não** edição de mapas.
- O extrator do Claude lê o APF completo na RAM e não valida todos os limites, tamanhos de saída ou caminhos de extração. Não usar sem revisão em fontes não confiáveis.

## Primeiro trabalho do Claude
Criar `tools/inspect_template.py` para análise **somente leitura** de `VuTemplateAsset/Levels/CityA`; comparar com `ParkA` e `FactoryA`. Investigar classes de entidades, offsets, transformações e referências. Gerar apenas metadados, não dumps de assets.

## Protocolo de conversa entre agentes
1. Ler `README.md`, `rearme.md`, `docs/RESEARCH_LOG.md` e as issues do projeto.
2. Responder à issue **[AGENTS] Coordenação ChatGPT ↔ Claude** com: observação, evidência (comandos e offsets), hipótese, tentativas falhas, próximo teste e pergunta ao outro agente.
3. Em cada modificação, atualizar `rearme.md` e `docs/RESEARCH_LOG.md`, informar testes executados e limites.
4. Trabalhar em branch/PR própria sempre que possível. Não fazer merge de hipóteses sem teste.

**Importante:** ChatGPT não recebe automaticamente mensagens do Claude e vice-versa. O usuário deve solicitar que cada agente leia as novas respostas da issue. Não há conversa direta em tempo real nesta integração.

Não publicar XAPK, APK, APF, binários, texturas, modelos ou cenas originais, nem tentar contornar DRM/anticheat ou serviços multiplayer.
