# Meta: reconstruir arenas ORIGINAIS completas no editor Android

**Prioridade definida pelo proprietário em 12/10/2026:** visualizar a arena inteira, original, com todos os recursos. Não adicionar cenários imaginados, água arbitrária ou texturas escolhidas por semelhança.

## Inventário confirmado em uma cópia XAPK original

Executado localmente:

```bash
python tools/scene_dependencies.py ~/storage/downloads/SEU_JOGO.xapk --out scene-audit.json
python -m unittest discover -s tests -p 'test_scene_dependencies.py' -v
```

- **9 `VuTemplateAsset/Levels`**: todos legíveis.
- **141/141 `VuWaterMapAsset`**: todos referenciados por strings de caminho exatas nas cenas, sem recurso aquático órfão nessa análise. Cabeçalhos reconhecidos: **135 DXT1** e **6 ETC1**. *São imagens/mapas de dados, não a geometria posicionada da água.*
- **409 referências diretas a `VuStaticModelAsset`** nos nove templates; **9 referências a modelos animados**, **28 a cubemaps**, **21 a lightmaps**, **31 a texturas** e **6 a materiais**. São **ocorrências por arena de nomes distintos**, não contagem de instâncias. Dependências aninhadas de prefabs podem aumentar esses números.
- As cenas contêm nomes de tipos `VuWaterSurfaceEntity`, `VuWaterRampEntity`, `VuInfiniteOceanWaveEntity` e `VuWaterTextureSettingsEntity` (nem todas as arenas usam todos). Suas posições, dimensões e atributos **ainda não foram decodificados**.

Ver [resumo por arena](water-scene-audit.json). O scanner não incorpora nenhum byte de modelo, imagem, APK ou APF ao resultado; apenas metadados e nomes de recursos. Código e testes usam fixtures sintéticas.

## Bloqueio técnico principal

A implementação da v0.8 importa principalmente malhas de `VuStaticModelAsset/Level`, com texturas difusas. Entretanto uma cena original é definida por um **grafo serializado de entidades e instâncias** no `VuTemplateAsset/Levels/<arena>`. Um modelo referenciado pode aparecer em múltiplas posições e rotações; fazer renderização só pelo nome do modelo não equivale à cena original.

O grafo ainda precisa ser interpretado para identificar:

1. Instâncias: tipo de entidade, caminho do modelo, matriz de posição/rotação/escala, hierarquia de pais, estado e visibilidade.
2. Água: instâncias `VuWaterSurfaceEntity`/`VuWaterRampEntity`, posição, largura, altura, geometria, material, lightmap e efeitos de onda. **Nunca preencher lacunas inventando planos azuis.**
3. Renderização: lightmaps, cubemaps, vertex colors, transparência, sky, vegetação, partículas, modelos animados, objetos interativos e shaders específicos.
4. Percurso: geometria física e visual corretamente alinhadas; eventualmente física aquática, checkpoints e rotas da IA (não necessário para uma visualização estática inicial).

## Critério de aceite para chamar “arena original completa”

- Sem objetos ou superfícies em posições adivinhadas.
- Modelos e instâncias posicionados a partir dos transforms originais;
- Todas as superfícies aquáticas e os principais recursos ambientais carregados;
- Texturas, iluminação e transparências em nível visual comparável ao jogo;
- Comparação de capturas de ângulos equivalentes entre o Renegade e a versão Android, anotando diferenças restantes por arena;
- Mostrar um relatório de cobertura quando recursos originais ainda não tiverem suporte.

**Status:** o objetivo é viável como investigação, **não está alcançado**. A primeira entrega que valeria denominar reconstrução de arena será um leitor de instâncias `VuTemplateAsset` com posição/rotação/escala validadas; o scanner deste marco apenas determina quais recursos são esperados.

## Próxima tarefa de implementação

Começar com `CityB` e um trecho pequeno. Extrair e provar o mapeamento exato entre uma entidade do `VuTemplateAsset`, um `VuStaticModelAsset` e seu transform; renderizar uma instância na posição correta. Depois aplicar o mesmo decoder às entidades aquáticas. Evitar liberar um APK “completo” antes dessas verificações.
