$vcvarsall = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat'

if (-not (Test-Path $vcvarsall)) {
    Write-Error "vcvarsall.bat not found at: $vcvarsall"
    exit 1
}

# Run vcvarsall in a cmd subshell, dump all env vars, then import them
# into the current PowerShell process.
cmd /c "`"$vcvarsall`" x64 > nul 2>&1 && set" | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
    }
}

Write-Host "MSVC x64 environment ready. You can now run 'cl' directly." -ForegroundColor Green
