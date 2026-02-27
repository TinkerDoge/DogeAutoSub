; DogeAutoSub Installer Script for Inno Setup

[Setup]
AppName=DogeAutoSub
AppVersion=1.0.0
AppPublisher=DogeAutoSub Team
AppPublisherURL=https://github.com/yourusername/DogeAutoSub
AppSupportURL=https://github.com/yourusername/DogeAutoSub/issues
AppUpdatesURL=https://github.com/yourusername/DogeAutoSub/releases
DefaultDirName={autopf}\DogeAutoSub
DefaultGroupName=DogeAutoSub
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename=DogeAutoSub-Setup-v1.0.0
SetupIconFile=icons\favicon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\DogeAutoSub\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DogeAutoSub"; Filename: "{app}\DogeAutoSub.exe"
Name: "{group}\{cm:UninstallProgram,DogeAutoSub}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DogeAutoSub"; Filename: "{app}\DogeAutoSub.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DogeAutoSub.exe"; Description: "{cm:LaunchProgram,DogeAutoSub}"; Flags: nowait postinstall skipifsilent
