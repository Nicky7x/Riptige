# Riptide Map Lab — Android v0.2.0-alpha (12/10/2026)

## Mudanças solicitadas pelo usuário

1. **Botões clicáveis e centralizados:** a tela nativa Java passou a respeitar os insets reais de status bar/notificações e navegação no Android 11+ (incluindo Android 15/target 35), com `setDecorFitsSystemWindows(false)` + listener de `WindowInsets`. Nas versões anteriores, usa `fitsSystemWindows`. Os botões Importar XAPK e Abrir editor aparecem lado a lado, com larguras iguais, alinhados ao centro e espaço de segurança superior.
2. **Arena completa montada:** a visualização 3D passa a carregar **todas as malhas de colisão validadas da arena selecionada ao mesmo tempo**, preservando a posição original de cada peça. Por exemplo, CityA = 9 malhas; CityB = 10. Seletor de trecho continua para edição detalhada; Focar seleção ajusta câmera sem esconder o resto. Checkbox "Arena completa (todas as malhas)" permite alternar entre cena inteira e trecho isolado. Botão Ver arena volta à montagem completa.
3. Versão atualizada para **0.2.0-alpha**, `versionCode=2`. Dados importados previamente continuam no armazenamento privado do app ao atualizar o APK.

## Escopo e limitações

"Unificar" significa **montagem visual no mesmo espaço 3D**, não fusão destrutiva dos arquivos originais. Mantemos cada malha separada para aplicar patches ao recurso correto. Exibimos colisões, não modelos visuais/texturas. Doze malhas da amostra original não foram validadas por divergências de formato. Nem o editor nem o APK alteram o jogo instalado; nenhum novo mapa in-game foi testado.

## Evidências de teste

- HTML pessoal da versão v0.2 gerado do XAPK privado: **9 arenas e 75 malhas compatíveis**.
- Chromium headless em viewport mobile (430×875), sem erros JavaScript: CityA = 9 visíveis, selecionar Zone03 continua 9, Focar seleção mantém 9, desmarcar Arena completa exibe 1, Ver arena restaura 9, CityB = 10 e alternância de volta preserva edição e exportação de patch.
- `node --check` passou nos 3 scripts JS modificados; Python `py_compile` passou no gerador.
- **A tela nativa com insets ainda precisará ser testada no Poco X8 Pro.** Resultado de compilação GitHub Actions será registrado separadamente.

## Build

Workflow: `.github/workflows/build-android.yml`, roda Gradle `:app:testDebugUnitTest :app:assembleDebug`; artefato `riptide-map-lab-android-debug` contém `app-debug.apk`. APK não contém assets do jogo; importa XAPK original localmente uma única vez.