param(
    [string]$JdkHome = 'C:\Program Files\Java\jdk-27',
    [string]$JarName = 'ifogsim-simulator.jar'
)
$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$classes = Join-Path $project 'build\classes'
$dist = Join-Path $project 'dist'
New-Item -ItemType Directory -Force -Path $classes, $dist | Out-Null
$sourceList = Join-Path $project 'build\sources.txt'
Get-ChildItem (Join-Path $project 'src') -Recurse -Filter '*.java' |
    ForEach-Object { '"' + $_.FullName.Replace('\', '/') + '"' } |
    Set-Content $sourceList -Encoding ascii
$classpath = "$project\jars\*;$project\jars\commons-math3-3.5\*"
& "$JdkHome\bin\javac.exe" -encoding UTF-8 -cp $classpath -d $classes "@$sourceList"
if ($LASTEXITCODE -ne 0) { throw 'Java compilation failed.' }
$dependencies = Get-ChildItem (Join-Path $project 'jars') -Recurse -Filter '*.jar' |
    ForEach-Object { '../' + $_.FullName.Substring($project.Length + 1).Replace('\', '/') }
$manifest = Join-Path $project 'build\MANIFEST.MF'
$classpathLine = 'Class-Path: ' + ($dependencies -join ' ')
$manifestLines = @('Manifest-Version: 1.0', 'Main-Class: org.fog.placement.IFogSimSocketServer')
while ($classpathLine.Length -gt 70) {
    $manifestLines += $classpathLine.Substring(0, 70)
    $classpathLine = ' ' + $classpathLine.Substring(70)
}
$manifestLines += $classpathLine
$manifestLines += ''
$manifestLines |
    Set-Content $manifest -Encoding ascii
$artifact = Join-Path $dist $JarName
& "$JdkHome\bin\jar.exe" --create --file $artifact --manifest $manifest -C $classes .
if ($LASTEXITCODE -ne 0) { throw 'JAR packaging failed.' }
Write-Host "Built: $artifact"
