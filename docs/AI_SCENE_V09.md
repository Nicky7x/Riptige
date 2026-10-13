# M1.20 / Android v0.9 — cenas GLB privadas e edição declarativa por IA

A v0.9 mantém **todos os recursos da v0.8** e adiciona um *modo de cena 3D instanciada* dentro do editor. Ele carrega GLB 2.0 **somente do armazenamento local escolhido pelo proprietário**; não inclui geometria comercial no APK ou no GitHub.

## Operação no Android

1. Instale a v0.9 e abra o editor normalmente. A importação de XAPK existente funciona como antes.
2. Toque **Mais → Abrir cena 3D (GLB)** e selecione a prévia **CityB_world_named_v09.glb**, baixada separadamente na Biblioteca privada do proprietário.
3. Em cena: toque para escolher um objeto próximo de seu pivô, ou use o campo **Buscar** para localizar caminho/mesh. Com um dedo gire; com dois dedos amplie ou diminua.
4. Mude X, Y ↑ ou Z do objeto selecionado e toque **Mover**; use **Duplicar** ou **Ocultar** para alterar a composição. **Cena JSON** exporta as mudanças como arquivo legível por IA.
5. Entregue o JSON exportado ao ChatGPT/Claude para propor alterações; peça para manter o formato e referências de modelos, alterando/removendo/adicionando entidades. De volta ao editor, carregue o **mesmo GLB** e use **Importar JSON** para aplicar.
6. **Voltar ✕** retorna à interface original sem modificar o XAPK.

Os eixos do modo GLB seguem o padrão **glTF Y-up** (Y é altura). O jogo original usa um referencial diferente; o exportador privado já o converte. O JSON é um *documento de autoria*, **não** um APF reconstruído nem uma arena jogável dentro do jogo.

## Esquema riptide-world-edit-v1

```json
{
  "format": "riptide-world-edit-v1",
  "version": 1,
  "units": "glTF_Y_UP",
  "assetSource": "user-selected-private-GLB",
  "entities": [
    {
      "id": "stable-object-id",
      "name": "My platform",
      "mesh": "Original mesh name from user's GLB",
      "meshIndex": 0,
      "matrix": [1,0,0,0, 0,1,0,0, 0,0,1,0, 10,5,20,1],
      "hidden": false
    }
  ]
}
```

**Os nomes acima são apenas exemplos.** Em arquivo real, `mesh` e `meshIndex` precisam apontar para a geometria correspondente no GLB selecionado. A IA pode clonar instâncias e ajustar matrizes, mas a v0.9 ainda **não** importa malhas inéditas diretamente do JSON. Para novos modelos 3D, precisamos implementar uma biblioteca de primitivas ou uma via de importação de GLB múltiplos.

Cada objeto tem `id` único, referência estável de mesh do GLB, matriz 4×4 **column-major** e flag `hidden`. A matriz inclui escala, rotação e translação nos índices 12/13/14; editar `matrix` permite à IA transformar instâncias sem duplicar bytes da geometria. O editor rejeita dimensões inválidas, NaN/Infinity, IDs repetidos, modelos desconhecidos e documentos com mais de 60.000 entidades. O arquivo é salvo localmente pelo Android Storage Access Framework.

## Desempenho / limites

O visualizador WebGL1 agrupa objetos por accessor de geometria e usa `ANGLE_instanced_arrays` quando disponível, com geometrias compartilhadas. A prévia CityB nomeada contém **2.658 instâncias**, mas somente **86 combinações distintas de buffers de posições/índices**. Sem suporte a instancing, existe fallback com limite de draw calls; o desempenho real no Poco ainda **não foi medido**.

O GLB CityB foi derivado localmente do XAPK fornecido pelo proprietário: 87 payloads de modelos decodificados, 2.658 instâncias exportadas, 160 instâncias estáticas ausentes e 14 entidades de água ainda não desenhadas. **Esta visualização GLB é sem texturas e sem água**, ao contrário da camada anterior v0.8 que aplica texturas difusas aos modelos de nível.

Nesta fase a seleção por toque usa o pivô projetado (centro de instância), não raycast por triângulo, e pode exigir zoom ou a ferramenta de busca. Efeitos, animações, água real e edição profunda da geometria ficam para as próximas versões.

## Testes

- `tests-js/world-v09.test.cjs` valida GLB 2.0 sintético, matrizes, hierarquia, JSON export/import com duas entidades, rejeição de matrizes inválidas e ponte do seletor SAF Android.
- O GLB pessoal da CityB foi parseado no Chromium: **2.658 nós, 86 buffers geométricos distintos**, sem erros de JavaScript no parsing. O Chromium do ambiente automatizado não disponibiliza WebGL; **não alegar que a renderização foi testada por GPU**.
- GitHub Actions compila unit tests Android e APK. Teste visual/touch no Poco é necessário.

## Próximos marcos

Integrar diretamente no Android a leitura dos templates/prefabs do XAPK (sem GLB intermediário) e reutilizar as texturas do importador v0.8 para instâncias; depois reconstruir água de `VuWaterSurfaceEntity` e permitir importar modelos externos/primitivas para cenas feitas do zero. Não misturar "visualizar no editor" com "aplicar ao jogo original".
