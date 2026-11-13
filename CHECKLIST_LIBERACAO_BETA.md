# Checklist de liberação v0.9

## Obrigatórios antes de enviar a terceiros
- [ ] Executar `testar_beta_windows.bat` sem falhas.
- [ ] Compilar com `build_windows.bat` no Windows.
- [ ] Gerar `installer_output/EditAI-Videos-JW-0.9.0-beta-Setup.exe`.
- [ ] Instalar em **outro Windows sem Python** e abrir pelo menu Iniciar.
- [ ] Importar MP4/MOV, exportar MP4 e validar áudio e legendas.
- [ ] Testar download, reabertura e desinstalação.
- [ ] Testar primeira execução e downloads de modelos de transcrição.
- [ ] Verificar licença e obrigações de redistribuição de FFmpeg, codecs, bibliotecas, fontes e modelos de IA; incluir avisos/licenças exigidos.
- [ ] Revisar política de privacidade: arquivos enviados à interface local, logs, cache, downloads de modelos e quaisquer conexões externas.
- [ ] Verificar alertas do Windows SmartScreen e decidir estratégia de assinatura de código.
- [ ] Calcular hash SHA-256 do instalador final e arquivar junto à versão.
- [ ] Definir canal de feedback e prazo do beta.

**Estado:** ainda não aprovado para distribuição externa até os itens acima serem verificados.
