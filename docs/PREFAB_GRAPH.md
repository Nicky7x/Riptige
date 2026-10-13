# Templates e prefabs originais — M1.17

**Análise read-only da cópia XAPK fornecida pelo proprietário. Nenhum recurso binário do jogo foi colocado no GitHub.**

As nove cenas contêm **23.544 instâncias** com tipo iniciando em `#`, apontando para **285 prefabs distintos**. Todos os 285 recursos `VuTemplateAsset/<nome>` estão presentes e foram decodificados pelo leitor da estrutura de templates. Essas definições contêm **38 referências distintas a prefabs aninhados**, e os 38 também têm recurso correspondente. Este teste não expande recursivamente toda a cadeia.

Nas definições consultadas, há **293 nomes distintos de `Model Asset`**, dos quais 291 correspondem a `VuStaticModelAsset`. Os outros dois (`Creatures/FishSchool`, `Vehicles/SmallPlane_skinned`) precisam de investigação como recursos potencialmente animados ou skinned. As **8 referências diretas distintas** a `Texture Asset` têm recurso correspondente. Esses números representam dependências, **não meshes ou objetos já renderizados**.

## Compressão LZMA1

No APF original, **38 templates LZMA1** descompactam com exatamente um byte NUL extra em relação ao tamanho declarado tanto no índice quanto no cabeçalho do template. `scene_dependencies.payload()` agora descarta esse byte **apenas** quando a classe é `VuTemplateAsset`, a compressão é LZMA1, o tamanho excede exatamente 1, o byte é `00` e o comprimento registrado no cabeçalho coincide com o índice. Tamanhos divergentes em outros casos continuam sendo rejeitados. Testes sintéticos validam a condição e a rejeição de byte final não-NUL.

## Como reproduzir no computador ou Termux

```sh
python tools/resolve_scene_prefabs.py /caminho/SEU_JOGO.xapk
python tools/resolve_scene_prefabs.py /caminho/SEU_JOGO.xapk --out /caminho/prefabs-privados.json
python -m unittest discover -s tests -p 'test_resolve_scene_prefabs.py' -v
```

Relatório agregado: [prefab-coverage-summary.json](prefab-coverage-summary.json). Não publique o JSON de `--out`, pois contém metadados originais extraídos da cópia do jogo.

**Próxima etapa:** compor transforms de pais/filhos do nível **e** do prefab, resolver os modelos visuais e posicionar cada instância no editor. Prefabs também podem conter modelos animados, folhagem, sprites e partículas, ainda não totalmente suportados. A v0.8 permanece o último APK funcional; esta etapa publicou apenas ferramentas e testes.