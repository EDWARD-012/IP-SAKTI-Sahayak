#Requires -Version 5.1
<#
.SYNOPSIS
  Download official open PDFs/HTML for IP-SAKTI corpus into data/raw and data/staging.
#>
$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Raw = Join-Path $Root 'data\raw'
$Staging = Join-Path $Root 'data\staging'
New-Item -ItemType Directory -Force -Path $Raw, $Staging | Out-Null

$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# source_id -> list of candidate URLs (first successful PDF/HTML wins)
$Sources = [ordered]@{
  'ayurveda-aahara-regs-2022' = @(
    'https://www.fssai.gov.in/upload/notifications/2022/05/62789a20b54bdGazette_Notification_Ayurveda_Aahara_09_05_2022.pdf'
  )
  'biological-diversity-act-2002-amendment-2023' = @(
    'https://egazette.gov.in/WritereadData/2023/247815.pdf'
  )
  'drugs-rules-1945' = @(
    'https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2022/drug_rules/Drugs%20Rules%201945_2024%2009.pdf'
  )
  'new-drugs-clinical-trials-rules-2019' = @(
    'https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2022/new_DC_rules/New%20Drugs%20and%20Clinical%20Trials%20Rules%2C%202019.pdf'
  )
  'dpdp-act-2023' = @(
    'https://www.meity.gov.in/static/uploads/2024/02/Digital-Personal-Data-Protection-Act-2023.pdf'
  )
  'nagoya-protocol' = @(
    'https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf',
    'https://www.cbd.int/doc/legal/cbd-en.pdf'
  )
  'trips-agreement' = @(
    'https://www.wto.org/english/docs_e/legal_e/27-trips.pdf',
    'https://www.wto.org/english/docs_e/legal_e/27-trips_01_e.htm'
  )
  'patents-act-1970' = @(
    'https://ipindia.gov.in/writereaddata/Portal/IPOAct/1_31_1_patent-act-1970-11march2015.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/15240/1/the_patents_act,_1970.pdf'
  )
  'gi-act-1999' = @(
    'https://ipindia.gov.in/writereaddata/Portal/IPOAct/1_49_1_gi-act-1999.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/1541/1/A1999-48.pdf'
  )
  'biological-diversity-act-2002' = @(
    'https://nbaindia.org/uploaded/act/BDACT_ENG.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/2046/1/A2003-18.pdf'
  )
  'drugs-cosmetics-act-1940' = @(
    'https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/acts_rules/2016DrugsandCosmeticsAct1940Rules1945.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/15386/1/a1940-23.pdf'
  )
  'tkdl-about' = @(
    'https://www.tkdl.res.in/tkdl/langdefault/common/Abouttkdl.asp?GL=Eng'
  )
}

function Test-IsPdf([string]$Path) {
  if (-not (Test-Path $Path)) { return $false }
  $len = (Get-Item $Path).Length
  if ($len -lt 1000) { return $false }
  $fs = [System.IO.File]::OpenRead($Path)
  try {
    $buf = New-Object byte[] 5
    [void]$fs.Read($buf, 0, 5)
    $sig = [System.Text.Encoding]::ASCII.GetString($buf)
    return $sig.StartsWith('%PDF')
  } finally { $fs.Close() }
}

$results = @()
foreach ($id in $Sources.Keys) {
  $ok = $false
  $destPdf = Join-Path $Raw "$id.pdf"
  $destHtml = Join-Path $Staging "$id.html"
  foreach ($url in $Sources[$id]) {
    Write-Host "`n==> $id" -ForegroundColor Cyan
    Write-Host "    $url"
    $tmp = Join-Path $Staging ("{0}.download" -f $id)
    try {
      & curl.exe -L --fail --retry 2 --connect-timeout 20 --max-time 180 `
        -A $UA -H "Accept: application/pdf,text/html,*/*" `
        -o $tmp $url 2>$null
      if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tmp)) {
        Write-Host "    FAIL curl exit=$LASTEXITCODE" -ForegroundColor Yellow
        continue
      }
      $size = (Get-Item $tmp).Length
      Write-Host "    downloaded $size bytes"
      if (Test-IsPdf $tmp) {
        # Map amendment / rules extras to staging; primary source_ids overwrite raw PDF
        $primary = @('ayurveda-aahara-regs-2022','nagoya-protocol','trips-agreement','patents-act-1970','gi-act-1999','biological-diversity-act-2002','drugs-cosmetics-act-1940')
        if ($primary -contains $id) {
          Move-Item -Force $tmp $destPdf
          Write-Host "    OK PDF -> data/raw/$id.pdf" -ForegroundColor Green
        } else {
          $stgPdf = Join-Path $Staging "$id.pdf"
          Move-Item -Force $tmp $stgPdf
          Write-Host "    OK PDF -> data/staging/$id.pdf" -ForegroundColor Green
        }
        $ok = $true
        break
      } else {
        # Likely HTML (TKDL about / WTO HTML)
        Move-Item -Force $tmp $destHtml
        Write-Host "    OK HTML -> data/staging/$id.html (not PDF)" -ForegroundColor Yellow
        $ok = $true
        break
      }
    } catch {
      Write-Host "    ERR $($_.Exception.Message)" -ForegroundColor Red
    }
  }
  $results += [pscustomobject]@{ source_id = $id; ok = $ok }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize
Write-Host "`nRaw PDFs:"
Get-ChildItem $Raw -Filter *.pdf -ErrorAction SilentlyContinue | Format-Table Name, Length
Write-Host "Staging:"
Get-ChildItem $Staging -ErrorAction SilentlyContinue | Format-Table Name, Length
