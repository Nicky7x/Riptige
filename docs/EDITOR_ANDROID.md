# Editor gráfico experimental para Android (versão alfa)

**Data:** 12/10/2026 • **Autor:** ChatGPT • **Origem:** análise da cópia privada do XAPK fornecida pelo usuário.

## O que funciona

- Extrair malhas de colisão de `VuCollisionMeshAsset/Level/...` com Python no Termux, sem root.
- Exibir vértices e triângulos em três projeções X/Y, X/Z e Y/Z numa interface gráfica responsiva.
- Tocar num vértice, editar X/Y/Z, arrastar com o dedo (opcional), desfazer/refazer.
- Exportar cópia `.edited.bin` com apenas os float32 editados, preservando demais bytes.
- Exportar `patch.json` com alterações comparadas ao arquivo original.
- Sem dependência de internet ao usar o editor localmente.

**Não funciona ainda:** reinserção do recurso no APF, edição da geometria visível, atualização de estruturas de aceleração de colisão, instalador de APK modificado, pistas novas jogáveis.

## Executar no Poco X8 Pro

Você precisa do Termux, do GitHub clonado e do seu próprio XAPK na pasta Download.

```bash
pkg update
pkg install git python -y
termux-setup-storage
git clone https://github.com/Nicky7x/Riptige.git
cd Riptige
python tools/export_collision.py \
  --source "$HOME/storage/downloads/com.vectorunit.silver.googleplay-104_arm64-v8a.xapk" \
  --track CityA --all \
  --out "$HOME/storage/downloads/RiptideMapLab"
python -m http.server 8765 --bind 127.0.0.1
```

Abra no navegador Android **http://127.0.0.1:8765/web/**. Em **Abrir malha**, escolha **Download/RiptideMapLab/CityA__Zone01_col.bin**. Selecione pontos e teste edições. Arquivos resultantes podem ser salvos pelo navegador no próprio aparelho.

O servidor é ligado somente no `127.0.0.1` do telefone; ele não deve ser aberto em interfaces de rede pública. É possível interrompê-lo com Ctrl+C no Termux.

## Evidência de estrutura

A amostra do usuário possui **87** recursos sob `VuCollisionMeshAsset/Level/`; **80/87** passaram a validação estrita do prefixo e dos triângulos. Os outros **7** apresentaram uma divergência de **1 byte** entre o tamanho de saída e o valor do índice APF, portanto foram marcados não validados.

Prefixo interpretado do recurso descompactado:

```text
u32 vertex_count
vertex_count × [float32 x, float32 y, float32 z, float32 w]  (w=0 nas amostras)
u32 index_count
index_count × u16 index  (index_count múltiplo de 3)
... campos adicionais AINDA DESCONHECIDOS
```

A malha `CityA/Zone01_col` contém **951 vértices** e **1620 triângulos**. Foram extraídas e verificadas **9/9 malhas de CityA**.

## Testes efetivamente realizados

- `python -m unittest discover -s tests -v` → **9 testes Python passaram** em ambiente local;
- `node tests-js/collision.test.cjs` → **suíte JavaScript passou** em ambiente local;
- `node --check web/app.js` e `node --check web/collision_core.js` → sintaxe OK;
- extração das 9 malhas de CityA → todas compatíveis com o parser;
- **não foi possível** realizar teste de navegação real automatizada no Chromium: política do ambiente bloqueou páginas `file://` e `http://127.0.0.1`. Ainda não há comprovação de execução no Poco do usuário.

## Pesquisa seguinte

1. Descobrir o significado dos dados após os índices de triângulos. Eles podem conter estruturas de colisão vinculadas à geometria.
2. Criar e testar round-trip do recurso sem alterações.
3. Decodificar referências de objetos e waypoints nos `VuTemplateAsset`.
4. Só depois, reconstruir uma cópia do APF/APK para teste offline controlado.

Nenhum binário proprietário é publicado. Referência de engenharia reversa de ferramenta para jogos Vector Unit: https://github.com/boyoftime/bbr-apf-studio (compatibilidade com Riptide não comprovada).
