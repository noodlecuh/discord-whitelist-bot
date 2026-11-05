import discord
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import json, os

load_dotenv(Path(__file__).parent / ".env")

TOKEN      = os.getenv("DISCORD_TOKEN")
DATA_FILE  = "whitelist.json"
CONFIG_FILE = "config.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=lambda b, m: get_cfg()["prefix"], intents=intents, help_command=None)

GREEN  = discord.Color.green()
RED    = discord.Color.red()
BLUE   = discord.Color.blurple()
ORANGE = discord.Color.orange()


def get_cfg():
    if not os.path.exists(CONFIG_FILE):
        return {"prefix": "!", "admin_role": "Admin", "whitelist_role": "whitelisted", "auto_kick": False,
                "embed": {"title": "✅ Whitelisted!", "description": "You are now whitelisted.", "color": "#57F287", "image_url": "", "footer": ""}}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def read():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def write(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def small_embed(desc, color):
    return discord.Embed(description=desc, color=color)

def whitelist_embed():
    cfg = get_cfg()["embed"]
    color_hex = cfg.get("color", "#57F287").lstrip("#")
    color = discord.Color(int(color_hex, 16))
    e = discord.Embed(title=cfg.get("title", ""), description=cfg.get("description", ""), color=color)
    if cfg.get("image_url"):
        e.set_image(url=cfg["image_url"])
    if cfg.get("footer"):
        e.set_footer(text=cfg["footer"])
    return e

def is_admin(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    cfg = get_cfg()
    if cfg["admin_role"]:
        return discord.utils.get(ctx.author.roles, name=cfg["admin_role"]) is not None
    return ctx.author.guild_permissions.manage_guild


@bot.event
async def on_ready():
    cfg = get_cfg()
    print(f"✓ {bot.user}  |  {len(read())} whitelisted  |  auto-kick={cfg['auto_kick']}")

@bot.event
async def on_member_join(member):
    cfg = get_cfg()
    if not cfg["auto_kick"] or str(member.id) in read():
        return
    try:
        await member.send(f"You are **not whitelisted** on **{member.guild.name}** and have been removed.")
    except discord.Forbidden:
        pass
    await member.kick(reason="Not on whitelist")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.strip().lower() == "wl":
        ctx = await bot.get_context(message)
        await wl_self(ctx)
        return
    await bot.process_commands(message)


@bot.command(name="test")
async def test(ctx):
    await ctx.send("bot is working")

@bot.command(name="wl")
async def wl_self(ctx):
    member = ctx.author
    cfg = get_cfg()
    data = read()
    role = discord.utils.get(ctx.guild.roles, name=cfg["whitelist_role"])

    if str(member.id) not in data:
        data[str(member.id)] = {"tag": str(member), "by": "self"}
        write(data)

    if role and role not in member.roles:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"[ROLE ERROR] {e}")

    await ctx.send(embed=whitelist_embed())


@bot.group(name="whitelist", invoke_without_command=True)
async def whitelist_group(ctx):
    await ctx.send(embed=small_embed("Use `wl` to whitelist yourself, or `!whitelist add/remove/list/check/clear`.", BLUE))

@whitelist_group.command(name="add")
async def wl_add(ctx, member: discord.Member):
    if not is_admin(ctx):
        return await ctx.send(embed=small_embed("❌ No permission.", RED))
    cfg = get_cfg()
    data = read()
    if str(member.id) in data:
        return await ctx.send(embed=small_embed(f"⚠️ {member.mention} is already whitelisted.", ORANGE))
    data[str(member.id)] = {"tag": str(member), "by": str(ctx.author)}
    write(data)
    role = discord.utils.get(ctx.guild.roles, name=cfg["whitelist_role"])
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"[ROLE ERROR] {e}")
    await ctx.send(embed=small_embed(f"✅ {member.mention} added to the whitelist.", GREEN))

@whitelist_group.command(name="remove")
async def wl_remove(ctx, member: discord.Member):
    if not is_admin(ctx):
        return await ctx.send(embed=small_embed("❌ No permission.", RED))
    cfg = get_cfg()
    data = read()
    if str(member.id) not in data:
        return await ctx.send(embed=small_embed(f"⚠️ {member.mention} is not on the whitelist.", ORANGE))
    del data[str(member.id)]
    write(data)
    role = discord.utils.get(ctx.guild.roles, name=cfg["whitelist_role"])
    if role and role in member.roles:
        await member.remove_roles(role)
    await ctx.send(embed=small_embed(f"🗑️ {member.mention} removed.", RED))

@whitelist_group.command(name="check")
async def wl_check(ctx, member: discord.Member):
    data = read()
    if str(member.id) in data:
        entry = data[str(member.id)]
        e = discord.Embed(title="✅ Whitelisted", color=GREEN)
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="User", value=member.mention)
        e.add_field(name="Added by", value=entry.get("by", "?"))
    else:
        e = discord.Embed(title="❌ Not Whitelisted", description=f"{member.mention} is not whitelisted.", color=RED)
    await ctx.send(embed=e)

@whitelist_group.command(name="list")
async def wl_list(ctx):
    if not is_admin(ctx):
        return await ctx.send(embed=small_embed("❌ No permission.", RED))
    data = read()
    if not data:
        return await ctx.send(embed=small_embed("📋 The whitelist is empty.", BLUE))
    lines = [f"<@{uid}>" for uid in data]
    for i in range(0, len(lines), 20):
        e = discord.Embed(title=f"📋 Whitelist — {len(data)} users", description="\n".join(lines[i:i+20]), color=BLUE)
        await ctx.send(embed=e)

@whitelist_group.command(name="clear")
async def wl_clear(ctx):
    if not is_admin(ctx):
        return await ctx.send(embed=small_embed("❌ No permission.", RED))
    count = len(read())
    write({})
    await ctx.send(embed=small_embed(f"🗑️ Cleared {count} entries.", ORANGE))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=small_embed("❌ Missing argument.", RED))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(embed=small_embed("❌ Member not found.", RED))
    elif not isinstance(error, commands.CommandNotFound):
        raise error


def start():
    bot.run(TOKEN)

if __name__ == "__main__":
    start()
