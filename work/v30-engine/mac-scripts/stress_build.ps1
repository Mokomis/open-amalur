$env:PYTHONIOENCODING='utf-8:replace'
foreach($r in 12000,24000,48000){ $d="work\v22-stress\r$r"; $sw=[Diagnostics.Stopwatch]::StartNew(); python -I work\v20-char\build_town.py $r $d > "work\v22-stress\r$r.log" 2>&1; "r$r rc=$LASTEXITCODE sec=$([int]$sw.Elapsed.TotalSeconds)" | Add-Content work\v22-stress\build-status.txt }
"done" | Add-Content work\v22-stress\build-status.txt
