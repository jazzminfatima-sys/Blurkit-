"""
dashboard.py
Panel web con FastAPI.
Muestra estadísticas en tiempo real del bot Blurkit.
Acceso: http://TU-IP:5000
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

# Importar estado compartido
from shared_state import state

app = FastAPI(
    title="BlurKit Dashboard",
    description="Panel de control para tu bot de Discord",
    version="1.0.0"
)

# ==============================================
# PLANTILLA HTML INTEGRADA
# ==============================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 BlurKit Bot - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        .pulse-dot { animation: pulse-dot 2s infinite; }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeIn 0.4s ease-out; }
        
        .log-line {
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1e293b; }
        ::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 4px; }
    </style>
</head>
<body class="bg-slate-900 text-white min-h-screen">
    
    <!-- HEADER -->
    <header class="bg-gradient-to-r from-blue-600 to-purple-600 shadow-lg">
        <div class="max-w-7xl mx-auto px-4 py-5">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="text-4xl">🤖</div>
                    <div>
                        <h1 class="text-2xl font-bold">BlurKit Bot Dashboard</h1>
                        <p class="text-blue-200 text-sm">Panel de control en tiempo real</p>
                    </div>
                </div>
                <div class="flex items-center gap-3 bg-white/10 px-4 py-2 rounded-full">
                    <span id="status-dot" class="w-3 h-3 rounded-full bg-yellow-400 pulse-dot"></span>
                    <span id="status-text" class="font-semibold">Conectando...</span>
                </div>
            </div>
        </div>
    </header>
    
    <!-- CONTENIDO PRINCIPAL -->
    <main class="max-w-7xl mx-auto px-4 py-8">
        
        <!-- TARJETAS DE ESTADÍSTICAS -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
            <div class="bg-slate-800 rounded-xl p-6 border-l-4 border-blue-500 hover:scale-105 transition-transform shadow-lg">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">📡 Servidores</p>
                        <p id="stat-guilds" class="text-3xl font-bold text-blue-400 mt-1">--</p>
                    </div>
                    <div class="text-4xl opacity-50">🏰</div>
                </div>
            </div>
            
            <div class="bg-slate-800 rounded-xl p-6 border-l-4 border-green-500 hover:scale-105 transition-transform shadow-lg">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">👥 Usuarios totales</p>
                        <p id="stat-members" class="text-3xl font-bold text-green-400 mt-1">--</p>
                    </div>
                    <div class="text-4xl opacity-50">👤</div>
                </div>
            </div>
            
            <div class="bg-slate-800 rounded-xl p-6 border-l-4 border-yellow-500 hover:scale-105 transition-transform shadow-lg">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">⚡ Latencia (Ping)</p>
                        <p id="stat-ping" class="text-3xl font-bold text-yellow-400 mt-1">-- ms</p>
                    </div>
                    <div class="text-4xl opacity-50">📶</div>
                </div>
            </div>
            
            <div class="bg-slate-800 rounded-xl p-6 border-l-4 border-purple-500 hover:scale-105 transition-transform shadow-lg">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-slate-400 text-sm">⏱️ Tiempo activo</p>
                        <p id="stat-uptime" class="text-3xl font-bold text-purple-400 mt-1">--</p>
                    </div>
                    <div class="text-4xl opacity-50">⏰</div>
                </div>
            </div>
        </div>
        
        <!-- FILA 2: Comandos + Info del bot -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
            <div class="bg-slate-800 rounded-xl p-6 border-l-4 border-pink-500 shadow-lg">
                <p class="text-slate-400 text-sm">📝 Comandos ejecutados</p>
                <p id="stat-commands" class="text-3xl font-bold text-pink-400 mt-1">0</p>
                <p id="stat-last-command" class="text-slate-500 text-xs mt-2 truncate">Último: --</p>
            </div>
            
            <div class="lg:col-span-2 bg-slate-800 rounded-xl p-6 border-l-4 border-cyan-500 shadow-lg">
                <p class="text-slate-400 text-sm mb-2">🤖 Información del bot</p>
                <div class="flex items-center gap-4">
                    <img id="bot-avatar" src="" alt="Avatar" class="w-16 h-16 rounded-full border-2 border-cyan-500 hidden">
                    <div>
                        <p id="bot-name" class="text-xl font-bold text-cyan-400">Cargando...</p>
                        <p class="text-slate-500 text-sm">Panel web corriendo en puerto 5000</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- FILA 3: Servidores + Logs -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <!-- Lista de servidores -->
            <div class="bg-slate-800 rounded-xl p-6 shadow-lg">
                <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
                    <span>🏰</span> Top Servidores
                    <span class="text-xs text-slate-500 font-normal">(por cantidad de miembros)</span>
                </h2>
                <div id="guilds-list" class="space-y-2 max-h-80 overflow-y-auto pr-2">
                    <p class="text-slate-500 text-sm">Cargando servidores...</p>
                </div>
            </div>
            
            <!-- Logs en vivo -->
            <div class="bg-slate-800 rounded-xl p-6 shadow-lg">
                <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
                    <span>📋</span> Registro de actividad
                    <span class="text-xs text-slate-500 font-normal">(últimos eventos)</span>
                </h2>
                <div id="logs-list" class="bg-slate-900 rounded-lg p-3 max-h-80 overflow-y-auto space-y-1">
                    <p class="text-slate-500 text-sm log-line">Esperando actividad...</p>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <footer class="mt-10 text-center text-slate-500 text-sm">
            <p>🎮 BlurKit Bot Dashboard • Actualizado cada 3 segundos</p>
            <p class="mt-1">FastAPI + discord.py • Python 3.13</p>
        </footer>
    </main>
    
    <script>
        async function actualizarDashboard() {
            try {
                const respuesta = await fetch('/api/stats');
                const datos = await respuesta.json();
                
                const dot = document.getElementById('status-dot');
                const texto = document.getElementById('status-text');
                
                if (datos.bot_ready) {
                    dot.className = 'w-3 h-3 rounded-full bg-green-400 pulse-dot';
                    texto.textContent = 'En línea';
                } else {
                    dot.className = 'w-3 h-3 rounded-full bg-red-400 pulse-dot';
                    texto.textContent = 'Desconectado';
                }
                
                document.getElementById('stat-guilds').textContent = datos.guild_count.toLocaleString();
                document.getElementById('stat-members').textContent = datos.member_count.toLocaleString();
                document.getElementById('stat-ping').textContent = datos.ping_ms + ' ms';
                document.getElementById('stat-uptime').textContent = datos.uptime;
                document.getElementById('stat-commands').textContent = datos.commands_used.toLocaleString();
                document.getElementById('stat-last-command').textContent = 'Último: ' + datos.last_command;
                
                document.getElementById('bot-name').textContent = datos.bot_user;
                const avatar = document.getElementById('bot-avatar');
                if (datos.bot_avatar) {
                    avatar.src = datos.bot_avatar;
                    avatar.classList.remove('hidden');
                }
                
                const guildsDiv = document.getElementById('guilds-list');
                if (datos.guilds_list && datos.guilds_list.length > 0) {
                    guildsDiv.innerHTML = datos.guilds_list.map(g => `
                        <div class="flex items-center gap-3 bg-slate-700/50 p-3 rounded-lg fade-in">
                            ${g.icon ? `<img src="${g.icon}" class="w-10 h-10 rounded-full">` : `<div class="w-10 h-10 rounded-full bg-slate-600 flex items-center justify-center text-lg">🏰</div>`}
                            <div class="flex-1 min-w-0">
                                <p class="font-semibold truncate">${g.name}</p>
                                <p class="text-slate-400 text-xs">${g.members.toLocaleString()} miembros</p>
                            </div>
                        </div>
                    `).join('');
                } else {
                    guildsDiv.innerHTML = '<p class="text-slate-500 text-sm">Aún no hay servidores</p>';
                }
                
                const logsDiv = document.getElementById('logs-list');
                if (datos.recent_logs && datos.recent_logs.length > 0) {
                    logsDiv.innerHTML = datos.recent_logs.map(log => 
                        `<p class="text-green-400 log-line">${log}</p>`
                    ).join('');
                }
                
            } catch (error) {
                console.error('Error actualizando:', error);
            }
        }
        
        actualizarDashboard();
        setInterval(actualizarDashboard, 3000);
    </script>
</body>
</html>
"""

# ==============================================
# RUTAS DEL PANEL
# ==============================================
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Página principal del dashboard."""
    return DASHBOARD_HTML

@app.get("/api/stats")
async def api_stats():
    """Endpoint JSON con todas las estadísticas."""
    return JSONResponse(content={
        "bot_ready": state.bot_ready,
        "bot_user": state.bot_user,
        "bot_avatar": state.bot_avatar,
        "guild_count": state.guild_count,
        "member_count": state.member_count,
        "ping_ms": state.ping_ms,
        "commands_used": state.commands_used,
        "uptime": state.get_uptime(),
        "last_command": state.last_command,
        "guilds_list": state.guilds_list,
        "recent_logs": state.recent_logs[:20]
    })

@app.get("/api/health")
async def health_check():
    """Verifica que el panel esté funcionando."""
    return {"status": "ok", "dashboard": "running", "bot_ready": state.bot_ready}
