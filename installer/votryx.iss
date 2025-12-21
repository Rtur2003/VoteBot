#define AppName "VOTRYX"
#define AppVersion "1.0.0"
#define AppPublisher "VOTRYX Contributors"
#define AppExeName "VOTRYX.exe"

[Setup]
AppId={{3E9A2C9E-1F7A-4A1A-9AB8-3C0D01B2D11C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={pf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=VOTRYX-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; Flags: unchecked

[Files]
Source: "..\dist\VOTRYX\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch VOTRYX"; Flags: nowait postinstall skipifsilent
