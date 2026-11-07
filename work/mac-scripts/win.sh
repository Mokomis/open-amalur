#!/bin/bash
# Run PowerShell from stdin on the Windows build machine.
# The PC moved to .59; its host keys match the ones known for .52.
T=$(mktemp); { printf '%s\n' '$ProgressPreference="SilentlyContinue";[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new();$R="C:\Users\rwill\Documents\Opem Amalur";Set-Location $R'; cat; } > "$T"
ENC=$(iconv -f UTF-8 -t UTF-16LE "$T" | base64 | tr -d '\n'); rm -f "$T"
ssh -o BatchMode=yes -o ConnectTimeout=10 -o HostName=192.168.68.59 -o HostKeyAlias=192.168.68.52 open-rune-windows "powershell -NoProfile -NonInteractive -EncodedCommand $ENC"
