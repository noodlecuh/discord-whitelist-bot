import discord
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import json, os

load_dotenv(Path(__file__).parent / ".env")

# ── config ───────────────────────────────────────────────────────────────────
TOKEN      = os.getenv("DISCORD_TOKEN")
PREFIX     = "!"
DATA_FILE       = "whitelist.json"
AUTO_KICK       = False         # kick on join if not whitelisted
ADMIN_ROLE      = "Admin"       # role allowed to run commands (or "" for manage_guild only)
WHITELIST_ROLE  = "whitelisted" # role to give/remove when adding/removing from whitelist
# ─────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
)

GREEN  = discord.Color.green()
RED    = discord.Color.red()
BLUE   = discord.Color.blurple()
ORANGE = discord.Color.orange()


# ── data helpers ─────────────────────────────────────────────────────────────

def read() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def write(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def embed(desc: str, color: discord.Color) -> discord.Embed:
    return discord.Embed(description=desc, color=color)


# ── permission guard ──────────────────────────────────────────────────────────

def is_admin(ctx: commands.Context) -> bool:
    if ctx.author.guild_permissions.administrator:
        return True
    if ADMIN_ROLE:
        return discord.utils.get(ctx.author.roles, name=ADMIN_ROLE) is not None
    return ctx.author.guild_permissions.manage_guild


# ── events ────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✓ {bot.user}  |  {len(read())} whitelisted  |  auto-kick={AUTO_KICK}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.strip().lower() == "wl":
        ctx = await bot.get_context(message)
        await wl_self(ctx)
        return
    await bot.process_commands(message)

@bot.event
async def on_member_join(member: discord.Member):
    if not AUTO_KICK or str(member.id) in read():
        return
    try:
        await member.send(
            f"You are **not whitelisted** on **{member.guild.name}** and have been removed.\n"
            "Contact a server admin to get added."
        )
    except discord.Forbidden:
        pass
    await member.kick(reason="Not on whitelist")


# ── commands ──────────────────────────────────────────────────────────────────

@bot.command(name="test")
async def test(ctx: commands.Context):
    await ctx.send("bot is working")

@bot.command(name="wl")
async def wl_self(ctx: commands.Context):
    member = ctx.author
    data = read()
    role = discord.utils.get(ctx.guild.roles, name=WHITELIST_ROLE)

    if str(member.id) not in data:
        data[str(member.id)] = {"tag": str(member), "by": "self"}
        write(data)

    if role:
        if role not in member.roles:
            try:
                await member.add_roles(role)
                print(f"[ROLE] Gave '{role.name}' to {member}")
            except Exception as e:
                print(f"[ROLE ERROR] {e}")
        else:
            print(f"[ROLE] {member} already has the role")
    else:
        print(f"[ROLE] Not found. Available: {[r.name for r in ctx.guild.roles]}")

    await ctx.send(embed=embed(f"✅ {member.mention} has been whitelisted.", GREEN))


@bot.group(name="whitelist", invoke_without_command=True)
async def whitelist_group(ctx: commands.Context):
    await ctx.send(embed=embed("Use `!wl` to whitelist yourself, or `!whitelist add/remove/list/check/clear`.", BLUE))


@whitelist_group.command(name="add")
async def wl_add(ctx: commands.Context, member: discord.Member):
    if not is_admin(ctx):
        return await ctx.send(embed=embed("❌ No permission.", RED))
    data = read()
    if str(member.id) in data:
        return await ctx.send(embed=embed(f"⚠️ {member.mention} is already whitelisted.", ORANGE))
    data[str(member.id)] = {"tag": str(member), "by": str(ctx.author)}
    write(data)
    role = discord.utils.get(ctx.guild.roles, name=WHITELIST_ROLE)
    if role:
        await member.add_roles(role)
    await ctx.send(embed=embed(f"✅ {member.mention} added to the whitelist.", GREEN))


@whitelist_group.command(name="remove")
async def wl_remove(ctx: commands.Context, member: discord.Member):
    if not is_admin(ctx):
        return await ctx.send(embed=embed("❌ No permission.", RED))
    data = read()
    if str(member.id) not in data:
        return await ctx.send(embed=embed(f"⚠️ {member.mention} is not on the whitelist.", ORANGE))
    del data[str(member.id)]
    write(data)
    role = discord.utils.get(ctx.guild.roles, name=WHITELIST_ROLE)
    if role and role in member.roles:
        await member.remove_roles(role)
    await ctx.send(embed=embed(f"🗑️ {member.mention} removed from the whitelist.", RED))


@whitelist_group.command(name="check")
async def wl_check(ctx: commands.Context, member: discord.Member):
    data = read()
    if str(member.id) in data:
        entry = data[str(member.id)]
        e = discord.Embed(title="✅ Whitelisted", color=GREEN)
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="User",     value=member.mention)
        e.add_field(name="Added by", value=entry.get("by", "?"))
    else:
        e = discord.Embed(title="❌ Not Whitelisted", description=f"{member.mention} is not on the whitelist.", color=RED)
    await ctx.send(embed=e)


@whitelist_group.command(name="list")
async def wl_list(ctx: commands.Context):
    if not is_admin(ctx):
        return await ctx.send(embed=embed("❌ No permission.", RED))
    data = read()
    if not data:
        return await ctx.send(embed=embed("📋 The whitelist is empty.", BLUE))
    lines = [f"<@{uid}>" for uid in data]
    # paginate at 20 per embed
    for i in range(0, len(lines), 20):
        chunk = lines[i:i+20]
        e = discord.Embed(
            title=f"📋 Whitelist — {len(data)} users",
            description="\n".join(chunk),
            color=BLUE,
        )
        await ctx.send(embed=e)


@whitelist_group.command(name="clear")
async def wl_clear(ctx: commands.Context):
    if not is_admin(ctx):
        return await ctx.send(embed=embed("❌ No permission.", RED))
    count = len(read())
    write({})
    await ctx.send(embed=embed(f"🗑️ Cleared {count} entries from the whitelist.", ORANGE))


# ── error handling ────────────────────────────────────────────────────────────

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=embed(f"❌ Missing argument. Use `{PREFIX}whitelist` for help.", RED))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(embed=embed("❌ Member not found — mention them directly.", RED))
    elif not isinstance(error, commands.CommandNotFound):
        raise error


# ─────────────────────────────────────────────────────────────────────────────

bot.run(TOKEN)
