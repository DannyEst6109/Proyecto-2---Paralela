# Abre Windows Terminal con Ubuntu (WSL), ejecuta cada sesion de scripts/sesion_evidencia.sh
# y guarda una captura de pantalla de la ventana en evidencias/<inciso>/<numero>_<sesion>.png.
# Uso (desde PowerShell, en la raiz del repositorio):
#   powershell -ExecutionPolicy Bypass -File scripts/capturar_pantallas.ps1 [-Sesiones compilacion,cifrado] [-Corte 30]
param(
    [string[]]$Sesiones = @("compilacion", "cifrado", "descifrado", "verificacion",
                            "clave_a", "clave_b", "clave_c", "pruebas"),
    [int]$Corte = 30
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Ventanas {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int cmd);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr w, IntPtr l);
    [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr hWnd, int attr, out RECT r, int size);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    public static IntPtr Buscar(string titulo) {
        IntPtr encontrada = IntPtr.Zero;
        EnumWindows((h, l) => {
            var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
            if (IsWindowVisible(h) && sb.ToString().Contains(titulo)) { encontrada = h; return false; }
            return true;
        }, IntPtr.Zero);
        return encontrada;
    }
}
"@
[Ventanas]::SetProcessDPIAware() | Out-Null

$raiz = Split-Path -Parent $PSScriptRoot
$raizWsl = (wsl.exe wslpath -a ($raiz -replace '\\', '/')).Trim()
$numeros = @{ compilacion = "01"; cifrado = "02"; descifrado = "03"; verificacion = "04";
              clave_a = "01"; clave_b = "02"; clave_c = "03"; pruebas = "04" }

foreach ($sesion in $Sesiones) {
    $inciso = if (@("compilacion", "cifrado", "descifrado", "verificacion") -contains $sesion) { "inciso1" } else { "inciso2" }
    $marca = "/tmp/evidencia_listo_$sesion"
    wsl.exe rm -f $marca | Out-Null
    $titulo = "Evidencia $sesion"
    # Al terminar, la sesion deja una marca y espera para que la ventana pueda capturarse.
    # Sin ';': Windows Terminal lo interpreta como separador de sus propios subcomandos.
    $comando = "cd '$raizWsl' && clear && (bash scripts/sesion_evidencia.sh $sesion $Corte || true) && touch $marca && sleep 600"
    Start-Process wt.exe -ArgumentList @("-w", "new", "--pos", "20,20", "--size", "132,40", "--title", "`"$titulo`"",
        "--suppressApplicationTitle", "wsl.exe", "-e", "bash", "-lc", "`"$comando`"")
    Write-Host "Ejecutando $sesion..."
    do { Start-Sleep -Seconds 1; wsl.exe test -f $marca } while ($LASTEXITCODE -ne 0)
    $ventana = [IntPtr]::Zero
    for ($i = 0; $i -lt 20 -and $ventana -eq [IntPtr]::Zero; $i++) { $ventana = [Ventanas]::Buscar($titulo); Start-Sleep -Milliseconds 250 }
    if ($ventana -eq [IntPtr]::Zero) { throw "No se encontro la ventana '$titulo'." }
    [Ventanas]::ShowWindow($ventana, 9) | Out-Null
    [Ventanas]::SetForegroundWindow($ventana) | Out-Null
    Start-Sleep -Milliseconds 800
    # DWMWA_EXTENDED_FRAME_BOUNDS (9) excluye la sombra invisible del borde.
    $r = New-Object Ventanas+RECT
    [Ventanas]::DwmGetWindowAttribute($ventana, 9, [ref]$r, 16) | Out-Null
    $ancho = $r.Right - $r.Left; $alto = $r.Bottom - $r.Top
    $imagen = New-Object System.Drawing.Bitmap $ancho, $alto
    $g = [System.Drawing.Graphics]::FromImage($imagen)
    # PrintWindow copia solo el contenido de la ventana: no incluye notificaciones ni otras
    # ventanas superpuestas. PW_RENDERFULLCONTENT (2) es necesario para Windows Terminal.
    $hdc = $g.GetHdc()
    [Ventanas]::PrintWindow($ventana, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc)
    $destino = Join-Path $raiz "evidencias\$inciso\$($numeros[$sesion])_$sesion.png"
    $imagen.Save($destino, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $imagen.Dispose()
    Write-Host "Captura: $destino"
    [Ventanas]::PostMessage($ventana, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null   # WM_CLOSE
    wsl.exe pkill -f "touch $marca && sleep 600" | Out-Null
    Start-Sleep -Seconds 1
}
