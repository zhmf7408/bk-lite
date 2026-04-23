$FilePath='{{config_file_path}}'

if (-not (Test-Path $FilePath -PathType Leaf)) {
  @{status='error'; error_type='file_not_found'; error='文件不存在'; size=0} | ConvertTo-Json -Compress
  exit 0
}

try {
  $fi = Get-Item $FilePath -ErrorAction Stop
} catch {
  @{status='error'; error_type='permission_denied'; error='无读取权限'; size=0} | ConvertTo-Json -Compress
  exit 0
}

$size = [int]$fi.Length
$bytes = [System.IO.File]::ReadAllBytes($FilePath)
for ($i = 0; $i -lt [Math]::Min($bytes.Length, 8192); $i++) {
  if ($bytes[$i] -eq 0) {
    @{status='error'; error_type='not_text'; error='非文本文件'; size=$size} | ConvertTo-Json -Compress
    exit 0
  }
}

$contentBase64 = [Convert]::ToBase64String($bytes)
@{status='success'; content_base64=$contentBase64; size=$size} | ConvertTo-Json -Compress
