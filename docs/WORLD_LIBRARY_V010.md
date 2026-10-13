# Biblioteca 3D privada — todas as arenas (v0.10 experimental)

O Riptide Map Lab passa a suportar uma biblioteca offline com os GLBs de **todas as 9 arenas** em vez de somente um CityB carregado manualmente. O material é gerado no próprio celular do proprietário a partir do XAPK original; não está no GitHub público.

## Gerar no Poco (Termux)

Instale Termux e rode:

```sh
pkg update
pkg install python git python-numpy -y
python -m pip install trimesh
termux-setup-storage
git clone --branch feature/all-arenas-world-library --single-branch https://github.com/Nicky7x/Riptige.git
cd Riptige
python tools/build_private_world_library.py \
  "$HOME/storage/downloads/SEU_JOGO.xapk" \
  --output "$HOME/storage/downloads/RiptideBiblioteca3D.zip"
```

O gerador usa numpy e trimesh, pode demorar e consumir espaço adicional, e nunca altera o XAPK. Consulte os pacotes da sua distribuição Termux se `python-numpy` não estiver disponível.

## Importar e trocar de arena

1. Baixe a build debug v0.10 no [GitHub Actions da branch experimental](https://github.com/Nicky7x/Riptige/actions/runs/38349960267), descompacte o artefato ZIP e instale o APK; depois e importe o XAPK como já fazia na v0.8/0.9.
2. No editor, abra **Mais → Importar biblioteca 3D (9 arenas)** e selecione somente o ZIP privado gerado (uma vez).
3. A biblioteca fica no armazenamento privado do Android. A arena selecionada será carregada automaticamente como GLB no mesmo viewport do editor; ao mudar de arena, o GLB correspondente será carregado.
4. O botão **Mundo 3D** reabre essa visualização quando fechada. O botão **Água: ligada/oculta** controla a camada de água aproximada.

## O que vem incluído

- `manifest.json` com as nove arenas e contagens por arena.
- `world/<Arena>.glb` para cada uma das nove cenas visuais estáticas, com instâncias e transformações.
- `water/<Arena>.json` com referências originais de água, transformações e dimensões decodificadas.

**Água:** renderização diagnóstica plana somente quando dimensões X/Y verificáveis estão presentes. Não são reconstruídas ondas, refração, topologia original ou a textura real de `VuWaterMapAsset`. Entidades sem dimensões são preservadas nos metadados, mas não são desenhadas; jamais inventamos tamanhos.

**Texturas:** as imagens difusas da v0.8 continuam na visualização de modelos antiga. Os GLBs do mundo reconstruído ainda não têm UV/materiais integrados; portanto v0.10 NÃO entrega o mundo totalmente texturizado. Este é um bloqueio técnico pendente.

**Outros componentes:** modelos animados, partículas, checkpoints, IA e efeitos especiais ainda não compõem a cena completa. A ordem Euler e pivôs permanecem hipóteses.

**Instalação:** builds debug do GitHub podem ter assinaturas distintas; o identificador v0.10 `.v10` permite instalar em paralelo, com necessidade de reimportar o XAPK e biblioteca. Nenhuma alteração no jogo original; não se afirma pista jogável.

## Contrato e segurança

Formato `riptide-private-world-library-v1`. O importador valida o manifesto, as nove entradas obrigatórias, caminhos e tamanhos. O WebView só serve os recursos de um ZIP offline guardado pelo aplicativo. Não publicar o ZIP, os GLBs nem JSONs originais no repositório.

## Pendências para uma reprodução fiel

Vincular UVs/materiais e texturas às instâncias; reconstruir geometria/material real da água; incorporar componentes animados, física e colisões visualmente coerentes; validar posições e desempenho no Poco X8 Pro. A cobertura completa ainda não está demonstrada.
