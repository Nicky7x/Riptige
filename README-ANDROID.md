# Riptide Map Lab para Android — versão alfa

Aplicativo Android nativo (Java + Android WebView) que hospeda o **editor 3D já desenvolvido**. Não há React nem bibliotecas JS baixadas na execução. O projeto público **não contém** assets do jogo nem APK/XAPK proprietários.

## Por que uma aplicação híbrida?

A interface de manipulação 3D e câmera orbital já foi construída em WebGL/Canvas. Refazê-la do zero em Kotlin/Java tomaria muito mais tempo sem acrescentar edição de objetos visuais. O aplicativo Android fornece integração com o sistema de arquivos, importação de XAPK, armazenamento privado e exportação de patches.

## Primeira utilização

1. Instale o APK gerado pelo GitHub Actions (debug não é uma versão publicada na Play Store).
2. Toque **Importar XAPK** e escolha sua cópia original do *Riptide GP: Renegade* no aparelho.
3. O aplicativo extrai **localmente** `base.apk/assets/Assets.apf`, procura malhas de colisão e incorpora os trechos reconhecidos ao editor 3D.
4. Depois disso, o JSON compactado com as arenas permanece **somente na pasta privada do aplicativo**. Nas próximas aberturas basta tocar em **Abrir editor**.
5. Use as ferramentas de movimentação para criar um patch; exporte `riptide-arenas-patch.json` escolhendo uma pasta de destino no seletor Android.

O aplicativo **não solicita acesso amplo ao armazenamento**, não pede root, não envia seus dados pela rede, não distribui assets e não modifica a instalação original do jogo. Se remover os dados do app, será preciso importar novamente.

**Escopo técnico:** o editor manipula **malhas de colisão**, ainda não os modelos visuais nem uma pista integralmente jogável. A importação APF v6 e LZMA1 é experimental; há recursos não suportados. O funcionamento e desempenho reais no Poco X8 Pro **não foram testados**. A variante no navegador continua disponível.

## Build no GitHub Actions

O workflow `.github/workflows/build-android.yml` utiliza Java 17, Gradle 8.13 e Android Gradle Plugin 8.13.2. Execute **Actions → Build Riptide Map Lab APK → Run workflow** e baixe o arquivo `riptide-map-lab-android-debug` na área **Artifacts** da execução bem-sucedida. Dentro do ZIP está `app-debug.apk`.

Para build local em computador com SDK Android e Gradle 8.13:

```sh
gradle -p android :app:testDebugUnitTest :app:assembleDebug
```

Os testes unitários usam fixtures **sintéticas**, sem bytes do jogo.

## Limitações dos testes

Sem SDK Android no ambiente de desenvolvimento atual não foi possível compilar/instalar um APK localmente. A lógica Java de leitura de geometria e descompressão zlib passou em um teste de compilação `javac` com stubs, que **não substitui** uma compilação real pelo Android Gradle Plugin. Até obter uma execução `assembleDebug` com sucesso no Actions, **não há APK pronto para instalar**.

## Próximas etapas

1. Fazer passar o primeiro `assembleDebug` remoto e os testes sintéticos.
2. Validar no Poco a importação do XAPK, o renderizador 3D e a exportação de patches.
3. Profiling de desempenho, tolerância aos 12 recursos ainda não suportados e progresso/feedback por fase.
4. Em paralelo, continuar engenharia reversa dos formatos de geometria visual e sistemas de água/IA, sem contornar integridade/DRM ou interferir em multiplayer.

Manter documentação do projeto em `README.md`, `rearme.md` e `CLAUDE.md`.