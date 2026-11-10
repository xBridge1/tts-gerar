; Instalador do Gerador de TTS (Inno Setup 6).
; Normalmente é compilado pelo build.ps1, que gera antes a pasta dist\GeradorTTS.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppName "Gerador de TTS"
#define AppExe "GeradorTTS.exe"

[Setup]
AppId={{97AD56FF-3421-4E04-8273-1D3C9F1662CC}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\Gerador TTS
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Instala sem pedir administrador; o usuário pode optar por instalar para todos.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=GeradorTTS-Setup-{#AppVersion}
SetupIconFile=icon\app.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\GeradorTTS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
