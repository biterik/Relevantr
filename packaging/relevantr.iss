; Inno Setup script for the Relevantr Windows installer.
; Compile from the repository root after `python build.py` produced
; dist\Relevantr\, passing the artifact version:
;   iscc /DAppVersion=2.0.0 packaging\relevantr.iss

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{9B5B36D1-6A6D-4E1B-9A57-5D6C2F2D64D2}
AppName=Relevantr
AppVersion={#AppVersion}
AppPublisher=Erik Bitzek
AppPublisherURL=https://github.com/biterik/Relevantr
AppSupportURL=https://github.com/biterik/Relevantr/issues
DefaultDirName={autopf}\Relevantr
DefaultGroupName=Relevantr
DisableProgramGroupPage=yes
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=Relevantr-{#AppVersion}-windows-x86_64-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "..\dist\Relevantr\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Relevantr"; Filename: "{app}\Relevantr.exe"
Name: "{autodesktop}\Relevantr"; Filename: "{app}\Relevantr.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Relevantr.exe"; Description: "{cm:LaunchProgram,Relevantr}"; Flags: nowait postinstall skipifsilent
