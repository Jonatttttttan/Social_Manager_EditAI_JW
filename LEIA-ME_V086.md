# EditAI Videos JW — v0.8.6 (preparacao beta)

## Alteracoes
- Corrigida a identidade do instalador: EditAI Videos JW, versao 0.8.6-beta, publicador Jonathan Willian Gonçales Alves.
- Corrigida a verificacao do nome do arquivo de instalacao gerado pelo Inno Setup.
- Atualizado o teste de instalacao para a pasta padrao da nova marca.
- Incluidos `auditoria_beta.py` e `testar_beta_windows.bat` para verificacoes estaticas e testes automatizados.
- Mantido o codigo de edicao e da interface da v0.8.5, sem alteracoes no motor de processamento.

## Fluxo recomendado
1. Configure Python 3.12 e coloque ffmpeg.exe e ffprobe.exe em bin/.
2. Execute `run_windows.bat` para validar edicao individual, legendas, audio e fila.
3. Execute `testar_beta_windows.bat` para auditoria e testes unitarios.
4. Execute `build_windows.bat`, teste `dist\PromptVideoAI\PromptVideoAI.exe` e exporte um MP4.
5. Instale Inno Setup 6 e execute `criar_instalador_windows.bat`.
6. Instale `installer_output\EditAI-Videos-JW-0.8.6-beta-Setup.exe` e valide atalhos, abertura, exportacao e desinstalacao em Windows sem Python.

## Checklist manual essencial
- MP4 e MOV: importar, editar, exportar e reproduzir o resultado.
- Legenda tradicional e dinamica, com os seis estilos, posicao e tamanho.
- Audio com silencio e audio normal, incluindo entrada com audio ausente.
- Processamento em lote com mais de um arquivo, ZIP e progresso.
- Nomes de arquivos com espacos e acentos, pasta sem permissao e disco com pouco espaco.
- Fechar e reabrir, executar offline apos instalacao, desinstalar.

**Limites:** auditoria estatica e testes unitarios nao garantem compatibilidade com todos os computadores Windows. A compilacao e a instalacao precisam ser validadas no Windows. Modelos Whisper podem exigir download na primeira utilizacao; testar o comportamento offline.
