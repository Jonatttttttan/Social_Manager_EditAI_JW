# EditAI Videos JW — v0.9 Beta Fechado

Baseada no código da v0.8.6. Esta versão concentra-se em empacotamento e documentação para testadores; não altera o motor de edição.

## Para o desenvolvedor
1. Extraia o ZIP em uma pasta nova.
2. Copie `ffmpeg.exe` e `ffprobe.exe` para `bin/` (não incluídos).
3. Execute `run_windows.bat` para teste local.
4. Execute `testar_beta_windows.bat`.
5. Execute `build_windows.bat` (requer Python 3.12).
6. Execute `criar_instalador_windows.bat` (requer Inno Setup 6).
7. Teste o instalador em um Windows sem Python.

Instalador esperado: `installer_output/EditAI-Videos-JW-0.9.0-beta-Setup.exe`.

O ZIP **não inclui** um instalador compilado nem FFmpeg. O aplicativo ainda precisa de validação em máquina limpa, verificação de licenças e revisão de privacidade antes de ser enviado a testadores.

Documentos: `GUIA_BETA_TESTADORES.md`, `FORMULARIO_FEEDBACK_BETA.md`, `CHECKLIST_LIBERACAO_BETA.md`.
