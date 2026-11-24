#define MyAppName "EditAI Videos JW"
#define MyAppVersion "0.9.8.4-beta2-social-manager"
#define MyAppExeName "PromptVideoAI.exe"
#define MyAppPublisher "Jonathan Willian Gonçales Alves"

[Setup]
AppId={{A4B18F0C-42B3-4D6E-9C37-2F7C42B84A01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\EditAI Videos JW
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=EditAI-Videos-JW-0.9.8.4-beta2-social-manager-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "dist\PromptVideoAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"

[Icons]
Name: "{group}\EditAI Videos JW"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\EditAI Videos JW"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir EditAI Videos JW"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Apenas arquivos temporários dentro da pasta do aplicativo, se existirem.
Type: filesandordirs; Name: "{app}\_tmp"
