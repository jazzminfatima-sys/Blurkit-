"""
bot.py
Blurkit Bot - Versión con DASHBOARD WEB integrado
✅ Tu código original se mantiene intacto
✅ Se agregó integración con panel web (FastAPI puerto 5000)
"""
import os
import re
import json
import asyncio
import datetime
import threading  # ✅ NUEVO: Para iniciar dashboard en segundo plano
import time       # ✅ NUEVO
from datetime import timezone, timedelta
import discord
from discord import app_commands
from discord.ext import commands, tasks  # ✅ AGREGADO: tasks
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# ==============================================
# ✅ NUEVO: IMPORTAR ESTADO COMPARTIDO (DASHBOARD)
# ==============================================
from shared_state import state
# Se cambia a all() para permitir la escucha de eventos de auditoría, hilos, roles y webhooks
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
# --- CONFIGURACIÓN CENTRAL ---
bot.BANNER_IP = "https://i.imgur.com/KrfKrBo.png"
bot.LOGO_BLURKIT = "https://i.imgur.com/ug6rEVD.png"
bot.ID_SERVIDOR_EXCLUSIVO = 454776569328566283  # Blurkit
bot.ID_SERVIDOR_CONTEO = 1214549433039982693  # Guardado por si tus Cogs lo usan internamente
bot.ID_ROL_STAFF_PERMISOS = 1353825860246835221
bot.ID_ROL_MOD_FALLBACK = 454786761663447050
bot.ID_ROL_BOOSTER = 601542293303984149
# ========== CONFIGURACION ESPECIAL MATRIMONIO ==========
CANAL_MATRIMONIO_ID = 1394950220541857844  # Canal donde TODOS pueden usar !marry y sus comandos
# Lista de comandos del sistema de matrimonio (para la excepcion en el check global)
COMANDOS_MATRIMONIO = {
    "marry", "casar", "casarse",
    "kiss", "hug", "slap", "cuddle", "feed", "shot"
}
ARCHIVO_HISTORIAL = "historial.json"
ARCHIVO_LOGS_CONFIG = "logs_config.json"
# --- FUNCIONES DE EXPEDIENTES ---
def cargar_historial():
    if not os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "w") as f:
            json.dump({}, f, indent=4)
        return {}
    try:
        with open(ARCHIVO_HISTORIAL, "r") as f:
            return json.load(f)
    except Exception:
        return {}
def guardar_historial(datos):
    with open(ARCHIVO_HISTORIAL, "w") as f:
        json.dump(datos, f, indent=4)
def registrar_sancion(user_id, tipo, moderador, razon, duracion):
    historial = cargar_historial()
    str_id = str(user_id)
    if str_id not in historial:
        historial[str_id] = []
    historial[str_id].append({
        "tipo": tipo, "moderador": moderador, "razon": razon, "duracion": duracion,
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    guardar_historial(historial)
    # ✅ NUEVO: Registrar en logs del dashboard
    state.add_log(f"🚨 Sanción: {tipo} | Usuario: {user_id} | Moderador: {moderador}")
def parse_duration_td(duration_str: str) -> datetime.timedelta:
    try:
        clean_str = duration_str.lower().strip()
        if clean_str.endswith('m'):
            return datetime.timedelta(minutes=int(clean_str[:-1]))
        elif clean_str.endswith('h'):
            return datetime.timedelta(hours=int(clean_str[:-1]))
        elif clean_str.endswith('d'):
            return datetime.timedelta(days=int(clean_str[:-1]))
        else:
            return datetime.timedelta(minutes=int(clean_str))
    except Exception:
        return datetime.timedelta(minutes=10)
async def buscar_usuario_dinamico(ctx, query: str):
    query = query.strip()
    clean_query = re.sub(r'[<@!>]', '', query)
    try:
        return await commands.MemberConverter().convert(ctx, query)
    except Exception:
        pass
    if clean_query.isdigit():
        uid = int(clean_query)
        target = ctx.guild.get_member(uid) or await ctx.guild.fetch_member(uid) if ctx.guild else None
        if target:
            return target
        try:
            return await bot.fetch_user(uid)
        except Exception:
            pass
    query_low = query.lower()
    return discord.utils.find(
        lambda m: query_low in m.name.lower() or (m.nick and query_low in m.nick.lower()),
        ctx.guild.members if ctx.guild else []
    )
# --- ALERTA DM ---
async def enviar_alerta_dm(usuario: discord.User, titulo: str, description: str, staff: str, razon: str, color: discord.Color):
    try:
        embed = discord.Embed(title=titulo, description=description, color=color)
        embed.add_field(name="🌐 Servidor", value="`Blurkit Network`", inline=True)
        embed.add_field(name="👮 Staff", value=staff, inline=True)
        embed.add_field(name="📝 Razón", value=f"```{razon}```", inline=False)
        link_apelacion = "https://docs.google.com/forms/d/e/1FAIpQLSecpa48dss5fFtWwrvcl3NrkGrdTc2MmLJ0y2tbH31FsX5HoQ/viewform"
        embed.add_field(
            name="⚖️ ¿Consideras que esto fue un error?",
            value=f"Presenta una solicitud formal aquí:\n👉 **[Formulario de Apelación]({link_apelacion})**",
            inline=False
        )
        embed.set_thumbnail(url=bot.LOGO_BLURKIT)
        embed.set_footer(text="Blurkit Network • Sistema de Seguridad", icon_url=bot.LOGO_BLURKIT)
        await usuario.send(embed=embed)
    except Exception:
        pass
def obtener_embed_no_permiso(bot_instance):
    embed = discord.Embed(
        title="🚫 ACCESO RESTRINGIDO",
        description="No tienes permiso para usar este comando.",
        color=discord.Color.red()
    )
    embed.add_field(name="🔒 Seguridad", value="Requiere Staff Directivo o rango explícito.")
    embed.set_thumbnail(url=bot_instance.LOGO_BLURKIT)
    return embed
# ✅ FUNCIONES DE PERMISOS SIMPLIFICADAS
def verificar_permisos_texto(ctx) -> bool:
    user_roles = [r.id for r in ctx.author.roles]
    if ctx.author.guild_permissions.administrator:
        return True
    if bot.ID_ROL_STAFF_PERMISOS in user_roles or bot.ID_ROL_MOD_FALLBACK in user_roles:
        return True
    return False
def verificar_permisos_comando(interaction: discord.Interaction) -> bool:
    user_roles = [r.id for r in interaction.user.roles]
    if interaction.user.guild_permissions.administrator:
        return True
    if bot.ID_ROL_STAFF_PERMISOS in user_roles or bot.ID_ROL_MOD_FALLBACK in user_roles:
        return True
    return False
# ========== ✅ NUEVO: DETECTAR SI ES COMANDO DE MATRIMONIO ==========
def _es_comando_matrimonio(ctx) -> bool:
    """Detecta si el comando invocado pertenece al sistema de matrimonio"""
    cmd_invocado = (ctx.invoked_with or "").lower()
    if cmd_invocado in COMANDOS_MATRIMONIO:
        return True
    
    contenido = (ctx.message.content or "").lower().strip()
    for cmd in COMANDOS_MATRIMONIO:
        if contenido.startswith(f"!{cmd}"):
            return True
    
    if ctx.command and hasattr(ctx.command, 'cog') and ctx.command.cog:
        nombre_cog = ctx.command.cog.__class__.__name__
        if "Marry" in nombre_cog or "Matrim" in nombre_cog:
            return True
    
    return False
# --- INTERCEPTOR GLOBAL ✅ CORREGIDO CON EXCEPCION DE MATRIMONIO ---
@bot.check
async def global_permissions_check(ctx):
    # 1) Canal especial sin restricciones
    if ctx.channel.id == 865282260507820062:
        return True
    
    # 2) Si el usuario tiene permisos generales (Staff/Admin) → pasar TODO
    if verificar_permisos_texto(ctx):
        return True
    
    # 3) ✅ EXCEPCION: COMANDOS DE MATRIMONIO
    if _es_comando_matrimonio(ctx):
        return True
    
    # 4) Si no es nada de lo anterior → sin permiso
    try:
        await ctx.send(embed=obtener_embed_no_permiso(bot), delete_after=8)
    except Exception:
        pass
    return False
bot.buscar_usuario_dinamico = buscar_usuario_dinamico
bot.verificar_permisos_texto = verificar_permisos_texto
bot.verificar_permisos_comando = verificar_permisos_comando
bot.obtener_embed_no_permiso = obtener_embed_no_permiso
bot.registrar_sancion = registrar_sancion
bot.enviar_alerta_dm = enviar_alerta_dm
bot.cargar_historial = cargar_historial
bot.parse_duration_td = parse_duration_td
# ==============================================================================
# 💻 SISTEMA CONSOLA (/consola + /say) · SOLO 4 ROLES STAFF AUTORIZADOS
# ==============================================================================
ROLES_STAFF_CONSOLA = [
    1504220839313408090,
    1454238161352917042,
    540178338233450546,
    1424107527443976273
]
class ConsolaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    def _tiene_permiso(self, usuario: discord.Member) -> bool:
        roles_usuario = [rol.id for rol in usuario.roles]
        for id_rol in ROLES_STAFF_CONSOLA:
            if id_rol in roles_usuario:
                return True
        return False
    @app_commands.command(
        name="consola",
        description="💻 Envia un mensaje por el bot como si fuera la consola"
    )
    @app_commands.describe(mensaje="Texto que quieres que envie el bot")
    async def cmd_consola(self, inter: discord.Interaction, mensaje: str):
        if not self._tiene_permiso(inter.user):
            embed = discord.Embed(
                title="🚫 ACCESO RESTRINGIDO",
                description="**NO TIENES PERMISO** para usar la consola del bot.\n\nSolo el Staff Autorizado puede ejecutar este comando.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=self.bot.LOGO_BLURKIT)
            embed.set_footer(text="Blurkit Network • Sistema de Seguridad", icon_url=self.bot.LOGO_BLURKIT)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        permisos = inter.channel.permissions_for(inter.guild.me)
        if not permisos.send_messages:
            embed = discord.Embed(
                title="⚠️ ERROR DE PERMISOS",
                description="El bot **NO tiene permiso** para enviar mensajes en este canal.",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Blurkit Network", icon_url=self.bot.LOGO_BLURKIT)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        embed_ok = discord.Embed(
            title="✅ MENSAJE ENVIADO CORRECTAMENTE",
            description="El bot envio tu mensaje al canal.",
            color=discord.Color.green()
        )
        embed_ok.add_field(name="📝 CONTENIDO", value="```" + mensaje[:1000] + "```", inline=False)
        embed_ok.add_field(name="💬 CANAL", value=inter.channel.mention, inline=True)
        embed_ok.add_field(name="👤 EJECUTADO", value=inter.user.mention, inline=True)
        embed_ok.set_footer(text="✅ APROBADO • Blurkit Network • Consola", icon_url=self.bot.LOGO_BLURKIT)
        await inter.response.send_message(embed=embed_ok, ephemeral=True)
        await inter.channel.send(mensaje)
        
        # ✅ NUEVO: Registrar en logs del dashboard
        state.add_log(f"💻 /consola | {inter.user} → #{inter.channel.name}: {mensaje[:60]}")
        
        print(
            "[CONSOLA] " + inter.user.name + " (" + str(inter.user.id) + ") "
            + "→ #" + inter.channel.name + ": " + mensaje[:80]
        )
    @app_commands.command(
        name="say",
        description="💬 Alias de /consola · Envia un mensaje por el bot"
    )
    @app_commands.describe(mensaje="Texto que quieres que envie el bot")
    async def cmd_say(self, inter: discord.Interaction, mensaje: str):
        await self.cmd_consola.callback(self, inter, mensaje)
# --- COMANDO ANUNCIO ---
@bot.tree.command(name="anuncio", description="Envía aviso de tradeo de ítems.")
async def cmd_anuncio_manual(interaction: discord.Interaction, canal: discord.TextChannel):
    if not verificar_permisos_comando(interaction):
        await interaction.response.send_message(embed=obtener_embed_no_permiso(bot), ephemeral=True)
        return
    embed = discord.Embed(
        description=(
            "# <a:Alerta:855211040363249724> TRADEO DE ÍTEMS \n\n"
            "<a:arrowrosa:1508331369279918161> Todo tradeo va en <#1405624528586936391>\n"
            "<:Bk:1105609191575535656> Tengan un lindo día."
        ),
        color=discord.Color.from_str("#008000")
    )
    embed.set_thumbnail(url=bot.LOGO_BLURKIT)
    await canal.send(embed=embed)
    await interaction.response.send_message("✅ Anuncio enviado.", ephemeral=True)
    state.add_log(f"📢 /anuncio enviado por {interaction.user} en #{canal.name}")
# --- SETUP HOOK ---
async def setup_hook():
    # ==================================================
    # ECONOMÍA PRINCIPAL
    # ==================================================
    try:
        await bot.load_extension("cogs.economia")
        print("[SISTEMA] ✅ Módulo ECONOMÍA cargado correctamente")
        state.add_log("✅ Módulo ECONOMÍA cargado")
    except Exception as e:
        print(f"\n[⚠️ ECONOMÍA] No se pudo cargar: {str(e)[:400]}\n")
        state.add_log(f"⚠️ ECONOMÍA falló: {str(e)[:80]}")
    # ==================================================
    # COGS FUNCIONALES
    # ==================================================
    await bot.load_extension("cogs.moderacion")
    await bot.load_extension("cogs.automod")
    await bot.load_extension("cogs.comandos")
    state.add_log("✅ Módulos: moderacion, automod, comandos")
    
    try:
        if "cogs.blurkit" not in bot.extensions:
            await bot.load_extension("cogs.blurkit")
            print("[SISTEMA] ✅ Módulo BLURKIT cargado correctamente (logs)")
            state.add_log("✅ Módulo BLURKIT cargado")
        else:
            print("[SISTEMA] ⚠️ BLURKIT ya estaba cargado - se evita duplicado")
    except Exception as e:
        print(f"\n[⚠️ BLURKIT] No se pudo cargar: {str(e)[:400]}\n")
    await bot.load_extension("cogs.addrole")
    await bot.load_extension("cogs.voice")
    await bot.load_extension("cogs.reportes")
    try:
        await bot.load_extension("cogs.borrar")
        print("[SISTEMA] ✅ Módulo BORRAR cargado correctamente")
        state.add_log("✅ Módulo BORRAR cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.borrar: {e}")
    try:
        await bot.load_extension("cogs.antilinks")
        print("[SISTEMA] ✅ Módulo ANTILINKS cargado correctamente")
        state.add_log("✅ Módulo ANTILINKS cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.antilinks: {e}")
    try:
        await bot.load_extension("cogs.vinculacion")
        print("[SISTEMA] ✅ Módulo VINCULACIÓN cargado correctamente")
        state.add_log("✅ Módulo VINCULACIÓN cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.vinculacion: {e}")
    try:
        await bot.load_extension("cogs.conteo")
        print("[SISTEMA] ✅ Módulo CONTEO cargado correctamente")
        state.add_log("✅ Módulo CONTEO cargado")
    except Exception as e:
        print(f"\n[⚠️ CONTEO] No se cargó: {str(e)[:150]}\n")
    try:
        await bot.load_extension("cogs.configuracion")
        print("[SISTEMA] ✅ Módulo CONFIGURACIÓN cargado correctamente")
        state.add_log("✅ Módulo CONFIGURACIÓN cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.configuracion: {e}")
    try:
        await bot.load_extension("cogs.autoroles")
        print("[SISTEMA] ✅ Módulo AUTOROLES cargado correctamente")
        state.add_log("✅ Módulo AUTOROLES cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.autoroles: {e}")
    try:
        await bot.load_extension("cogs.reacciones")
        print("[SISTEMA] ✅ Módulo REACCIONES cargado correctamente")
        state.add_log("✅ Módulo REACCIONES cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.reacciones: {e}")
    try:
        await bot.load_extension("cogs.bienvenida")
        print("[SISTEMA] ✅ Módulo BIENVENIDA cargado correctamente")
        state.add_log("✅ Módulo BIENVENIDA cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.bienvenida: {e}")
    
    # ✅ MATRIMONIO - Proteccion anti-duplicado
    try:
        if "cogs.marry" not in bot.extensions:
            await bot.load_extension("cogs.marry")
            print("[SISTEMA] ✅ Módulo MATRIMONIO cargado correctamente")
            state.add_log("✅ Módulo MATRIMONIO cargado")
        else:
            print("[SISTEMA] ⚠️ MATRIMONIO ya estaba cargado - se evita duplicado")
    except Exception as e:
        print(f"\n[⚠️ MATRIMONIO] No se pudo cargar: {str(e)[:400]}\n")
    try:
        await bot.load_extension("cogs.cumple")
        print("[SISTEMA] ✅ Módulo CUMPLEAÑOS cargado correctamente")
        state.add_log("✅ Módulo CUMPLEAÑOS cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.cumple: {e}")
    try:
        await bot.load_extension("cogs.sistema_boosts")
        print("[SISTEMA] ✅ Módulo SISTEMA BOOSTS cargado correctamente")
        state.add_log("✅ Módulo SISTEMA BOOSTS cargado")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar cogs.sistema_boosts: {e}")
    try:
        await bot.load_extension("cogs.chat")
        print("[SISTEMA] ✅ Módulo CHAT ROL + ALERTAS cargado correctamente")
        state.add_log("✅ Módulo CHAT cargado")
    except Exception as e:
        print(f"\n[⚠️ CHAT] No se cargó: {str(e)[:200]}\n")
    try:
        await bot.load_extension("cogs.actualizaciones")
        print("[SISTEMA] ✅ actualizaciones.py cargado (cogs/)")
        state.add_log("✅ Módulo ACTUALIZACIONES cargado")
    except Exception:
        try:
            await bot.load_extension("actualizaciones")
            print("[SISTEMA] ✅ actualizaciones.py cargado (raíz)")
        except Exception as e:
            print(f"[⚠️ ALERTA] No se encontró actualizaciones.py: {e}")
    # ==================================================
    # 💎 SISTEMA DE TRADEOS GENS OP
    # ==================================================
    try:
        if "cogs.gens_op" not in bot.extensions:
            await bot.load_extension("cogs.gens_op")
            print("[SISTEMA] ✅ Módulo GENS OP cargado correctamente · Tradeos Blurkit")
            print("[SISTEMA] ✅ Comandos: /trades_panel · /agregar · /cerrar · /tradeos_adm")
            print("[SISTEMA] ✅ Categoría: 1405347633194733588 · Logs: 1480811907933016165")
            state.add_log("✅ Módulo GENS OP cargado · Tradeos")
        else:
            print("[SISTEMA] ⚠️ GENS OP ya estaba cargado - se evita duplicado")
    except Exception as e:
        print(f"\n[⚠️ GENS OP] No se pudo cargar: {str(e)[:400]}\n")
    # ==================================================
    # SISTEMA CONSOLA (/consola + /say)
    # ==================================================
    try:
        await bot.add_cog(
            ConsolaCog(bot),
            guild=discord.Object(id=bot.ID_SERVIDOR_EXCLUSIVO)
        )
        print("[SISTEMA] ✅ Módulo CONSOLA cargado correctamente · /consola · /say")
        print("[SISTEMA] ✅ Permisos Consola: SOLO 4 ROLES STAFF autorizados")
        state.add_log("✅ Módulo CONSOLA cargado · /consola /say")
    except Exception as e:
        print(f"[⚠️ ERROR] No se pudo cargar el Sistema Consola: {e}")
    try:
        await bot.load_extension("cogs.anti_scam")
        print("[SISTEMA] ✅ Módulo ANTI-SCAM cargado · 10min · 1/2 → 2/2 · Canal 1424865903341867139")
        state.add_log("✅ Módulo ANTI-SCAM cargado")
    except Exception as e:
        print(f"\n[⚠️ ANTI-SCAM] No se pudo cargar: {str(e)[:250]}\n")
    try:
        await bot.load_extension("cogs.ventas")
        print("[SISTEMA] ✅ Módulo VENTAS cargado · Borra+DM+Logs+3Avisos→Mute5min")
        print("[SISTEMA] ✅ Categorías: 888987045568077884 · 1437983475511853127")
        print("[SISTEMA] ✅ Logs Staff: 1424865903341867139 · Canal OK: 1405624528586936391")
        state.add_log("✅ Módulo VENTAS cargado")
    except Exception as e:
        print(f"\n[⚠️ VENTAS] No se pudo cargar: {str(e)[:250]}\n")
    try:
        await bot.load_extension("cogs.meritos")
        print("[SISTEMA] ✅ Módulo MÉRITOS cargado · Tops 00:15AM Perú/Colombia · Canal 1494488667216154654")
        state.add_log("✅ Módulo MÉRITOS cargado")
    except Exception as e:
        print(f"\n[⚠️ MÉRITOS] No se pudo cargar: {str(e)[:250]}\n")
    try:
        await bot.load_extension("cogs.staffvoice")
        print("[SISTEMA] ✅ Módulo STAFF VOICE cargado · Canales temporales automáticos")
        print("[SISTEMA] ✅ Hub: 1532595605656834069 · Categoría: 1414712931144175839")
        print("[SISTEMA] ✅ Rol autorizado: 454786761663447050 · Comandos: /temporal")
        state.add_log("✅ Módulo STAFF VOICE cargado")
    except Exception as e:
        print(f"\n[⚠️ STAFF VOICE] No se pudo cargar: {str(e)[:250]}\n")
    try:
        await bot.load_extension("cogs.config_permisos")
        print("[SISTEMA] ✅ Módulo CONFIG PERMISOS cargado · /configurar_tickets")
        print("[SISTEMA] ✅ Aplica TEXTO+VOZ+FOROS a toda categoría · Auto canales nuevos 24/7")
        print("[SISTEMA] ✅ Gana al otro bot: sobrescribe permisos 0.5s después de que cree el canal")
        state.add_log("✅ Módulo CONFIG PERMISOS cargado")
    except Exception as e:
        print(f"\n[⚠️ CONFIG PERMISOS] No se pudo cargar: {str(e)[:250]}\n")
bot.setup_hook = setup_hook
# ============================================================
# ✅ NUEVO: TAREA PERIÓDICA PARA ACTUALIZAR DASHBOARD
# ============================================================
@tasks.loop(seconds=15)
async def actualizar_stats_dashboard():
    """Actualiza las estadísticas cada 15 segundos para el panel web."""
    if not bot.is_ready():
        return
    
    state.guild_count = len(bot.guilds)
    state.member_count = sum(g.member_count or 0 for g in bot.guilds)
    state.ping_ms = round(bot.latency * 1000, 1)
    
    # Actualizar lista de servidores (top 10 por miembros)
    guilds_sorted = sorted(bot.guilds, key=lambda g: g.member_count or 0, reverse=True)[:10]
    state.guilds_list = [
        {
            "name": g.name,
            "members": g.member_count or 0,
            "icon": g.icon.url if g.icon else "",
            "owner": str(g.owner) if g.owner else "Desconocido"
        }
        for g in guilds_sorted
    ]
# --- ON READY ---
@bot.event
async def on_ready():
    # ✅ NUEVO: Actualizar estado compartido para dashboard
    state.bot_ready = True
    state.bot_user = str(bot.user)
    state.bot_avatar = bot.user.avatar.url if bot.user.avatar else ""
    state.start_time = datetime.datetime.now()
    
    print(f'-----\n✅ Conectado: {bot.user}\n-----')
    print(f"🌐 Dashboard web disponible en: http://localhost:5000")
    state.add_log(f"🤖 Bot conectado como {bot.user}")
    
    # ✅ NUEVO: Iniciar la tarea de actualización de stats
    actualizar_stats_dashboard.start()
    
    try:
        g_blurkit = discord.Object(id=bot.ID_SERVIDOR_EXCLUSIVO)
        bot.tree.copy_global_to(guild=g_blurkit)
        await bot.tree.sync(guild=g_blurkit)
        print("[SYNC] ✅ Todos los comandos sincronizados en BLURKIT NETWORK")
        state.add_log("✅ Comandos sincronizados en Blurkit Network")
    except Exception as e:
        print(f"[SYNC] ❌ Falló la sincronización en Blurkit: {e}")
        state.add_log(f"❌ Sync falló: {str(e)[:60]}")
# --- ON MESSAGE ✅ ESTE ESTA BIEN, NO CAUSA DUPLICACION ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
# ============================================================
# ✅ NUEVO: CONTAR COMANDOS USADOS PARA EL DASHBOARD
# ============================================================
@bot.event
async def on_command_completion(ctx):
    """Se ejecuta cada vez que un comando se completa exitosamente."""
    state.commands_used += 1
    state.last_command = f"{ctx.command.name} (por {ctx.author})"
# --- ON COMMAND ERROR ✅ ACTUALIZADO ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, commands.CheckFailure):
        if _es_comando_matrimonio(ctx):
            return
        print(f"[CheckFailure] {ctx.command}: {error}")
        return
    
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        embed = discord.Embed(
            title="⚠️ Argumento incorrecto",
            description="Revisa el uso correcto del comando.\nSi tienes dudas, contacta a un miembro del Staff.",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=bot.LOGO_BLURKIT)
        try:
            await ctx.send(embed=embed)
        except Exception:
            pass
        return
    
    print(f"[CMD ERROR] {ctx.command}: {type(error).__name__}: {error}")
    state.add_log(f"❌ Error en {ctx.command}: {type(error).__name__}")
    try:
        await ctx.send(f"❌ Error: `{type(error).__name__}: {error}`", delete_after=15)
    except Exception:
        pass
# ============================================================
# ✅ NUEVO: INICIAR DASHBOARD EN HILO SEPARADO
# ============================================================
def iniciar_dashboard():
    """Inicia el servidor FastAPI en segundo plano."""
    time.sleep(2)  # Esperar un poco antes de iniciar
    try:
        import uvicorn
        from dashboard import app
        print("[DASHBOARD] 🌐 Iniciando panel web en puerto 5000...")
        uvicorn.run(app, host="0.0.0.0", port=5000, log_level="warning")
    except Exception as e:
        print(f"[DASHBOARD] ❌ Error al iniciar panel: {e}")
# ==============================================================================
# 🚀 ARRANCAR BOT (1 SOLA VEZ) · CON MANEJO DE ERROS LIMPIO
# ==============================================================================
if __name__ == "__main__":
    if not TOKEN:
        print("\n❌ ERROR: No se encontró DISCORD_TOKEN en el archivo .env")
        print("👉 Crea un archivo .env con: DISCORD_TOKEN=tu_token_aqui\n")
        exit(1)
    
    # ✅ NUEVO: Iniciar dashboard en hilo separado ANTES del bot
    dashboard_thread = threading.Thread(target=iniciar_dashboard, daemon=True)
    dashboard_thread.start()
    print("[SISTEMA] 🧵 Hilo del dashboard iniciado")
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"\n❌ ERROR CRITICO AL INICIAR BOT: {e}\n")
        state.add_log(f"❌ ERROR CRÍTICO: {str(e)[:80]}")
        exit(1)
