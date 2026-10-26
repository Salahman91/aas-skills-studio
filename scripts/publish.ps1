# ينشر المشروع على GitHub باستخدام رمز وصول (PAT) يملك صلاحية repo.
# لا يُخزَّن الرمز في إعدادات Git ولا في أي ملف.
#
# مثال:
#   .\scripts\publish.ps1 -Token ghp_xxx -RepoName aas-skills-studio -Public
#
param(
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$RepoName = "aas-skills-studio",
    [string]$Description = "Bilingual (AR/EN) desktop browser for the agentic-awesome-skills library",
    [switch]$Public
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $headers = @{
        Authorization          = "Bearer $Token"
        "User-Agent"           = "aas-skills-studio-publish"
        "Accept"               = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    Write-Host "→ التحقق من الحساب…"
    $me = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
    Write-Host ("  الحساب: " + $me.login)

    $fullName = "$($me.login)/$RepoName"
    Write-Host "→ التأكد من وجود المستودع $fullName …"
    $exists = $true
    try {
        Invoke-RestMethod -Uri "https://api.github.com/repos/$fullName" -Headers $headers | Out-Null
    } catch {
        $exists = $false
    }

    if (-not $exists) {
        Write-Host "→ إنشاء المستودع…"
        $body = @{
            name        = $RepoName
            description = $Description
            private     = (-not $Public)
            has_issues  = $true
            has_wiki    = $false
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Headers $headers `
            -Method Post -Body $body -ContentType "application/json" | Out-Null
        Write-Host "  تم الإنشاء."
    } else {
        Write-Host "  المستودع موجود مسبقاً."
    }

    Write-Host "→ ضبط الفرع الرئيسي والدفع…"
    git branch -M main 2>$null
    git remote remove origin 2>$null
    git remote add origin "https://github.com/$fullName.git"

    $authHeader = "AUTHORIZATION: bearer $Token"
    git -c http.extraheader="$authHeader" push -u origin main

    Write-Host ""
    Write-Host ("تم النشر: https://github.com/" + $fullName)
} finally {
    Pop-Location
}
