from src.ritV import ritV
import src.styles as styles
from src.errors import *
import discord
from discord.ext import commands, tasks
from discord.utils import get
import datetime
import aiohttp
import time
from rich.console import Console
import argparse
import os
import pickle
from rich.prompt import Prompt
import json

parser = argparse.ArgumentParser()
parser.add_argument('--no-resync', action='store_true', help='Skip synchronizing commands for quick debugging.')
debug_args = parser.parse_args()

console= Console()

verif = ritV(console)

if os.path.exists('bot.credentials'):
    with open('bot.credentials', 'rb') as file:
        token,server_name = pickle.load(file)
else:
    token = Prompt.ask("[bold]Initial bot setup:[not bold]\n↳ Please enter a Discord token")
    console.print('For the next steps, [bold]please make sure that your Minecraft Server is running[not bold] and that [bold]RCON is enabled[not bold]on the default port.')
    server_name = Prompt.ask("↳ Please enter the name of this server.")
    
    with open('bot.credentials', 'wb') as file:
        pickle.dump((token,server_name), file)

bot = commands.Bot(intents=discord.Intents.all())
bot.auto_sync_commands = False
guilds=["1182047934750142524"]
invites = {}
setup_panels = {}
setup_status_panels = {}
embed_credits = discord.Embed(title="⟶ keeping communities safer.",description="a  verification solution developed, hosted, and maintained by [mae.red](https://mae.red). please consider **[donating](https://www.buymeacoffee.com/maedotred)** to support my efforts :)",color=discord.Color.from_rgb(255,255,255))

async def fetch_hooks_channel(guild:discord.Guild) -> discord.TextChannel: 
    with open(f'./configs/{guild.id}.json', 'r') as file:
        config = json.load(file)    
    channel_hooks = await bot.fetch_channel(config['hooks_channel'])
    return channel_hooks

async def fetch_mod_channel(guild:discord.Guild) -> discord.TextChannel: 
    with open(f'./configs/{guild.id}.json', 'r') as file:
        config = json.load(file)
    channel_mod = await bot.fetch_channel(config['mod_channel'])
    return channel_mod

async def fetch_mod_role(guild:discord.Guild) -> discord.Role: 
    with open(f'./configs/{guild.id}.json', 'r') as file:
        config = json.load(file)
    return guild.get_role(config['mod_role'])

async def memberAlert(title:str, member:discord.Member,description=None):
    '''Warn the mod chat with information about a member.'''
    channel_mod = await fetch_mod_channel(member.guild)
    warn = discord.Embed(title=title,color=discord.Colour.red(),timestamp=datetime.datetime.now())
    if description:
        warn.description = description
    warn.set_thumbnail(url=member.avatar.url)
    warn.add_field(name='Name',value=member.name)
    warn.add_field(name='Mention',value=f'<@{member.id}>')    
    try:
        await channel_mod.send(embed=warn)
    except:
        try:
            await channel_mod.send(f'[Embed failure - please check permissions.]\n**{title}**\n<@{member.id}>')
        except Exception as e:
            await dev_logs_channel.send(f'Error: Failed to send ban alert embed or message for <@{member.id}> in {member.guild.name}, likely due to a permissions error.```{e}```')
    try:
        warn.title.replace('your server',member.guild.name)
        await dev_logs_channel.send(embed=warn)
    except:
        pass
                
async def ban_alt_list(guild:discord.Guild,banned_ids=verif.fetch_banlist(),reason_message='A new alt account was banned from your server.'):
    time_start = time.time()
    channel_hooks = await fetch_hooks_channel(guild)
    i = 0
    current_ban_ids = []
    async for ban_entry in guild.bans():
        current_ban_ids.append(ban_entry.user.id)
    for user_id in banned_ids:
        if user_id not in current_ban_ids:
            user = await bot.get_or_fetch_user(user_id)
            member= guild.get_member(user_id)
            if member is not None: # check if member is in server by getting a member object
                await memberAlert(reason_message,member) # alert that the member existed in the server
            await guild.ban(user, reason="Banned for the use of alternative accounts.")  # ban the member
            i += 1
    
    time_exec = time.time() - time_start
    logEmbed = discord.Embed(title='Ban list reloaded.',description=f'**{len(banned_ids)}** total entries, **{i}** new bans in this server.',color=discord.Color.blurple())
    logEmbed.set_footer(text=f'Completed in {time_exec:.2f} seconds.')
    try:
        await channel_hooks.send(embed=logEmbed)
    except:
        try:
            await channel_hooks.send(f'[Embed failure - please check permissions.]\n**{logEmbed.title}**\n{logEmbed.description}')
        except Exception as e:
            await dev_logs_channel.send(f'Error: Failed to send log embed or message for {logEmbed.description}, likely due to a permissions error.```{e}```')
    return i

@tasks.loop(seconds=15)
async def refreshInvites():
    for guild in bot.guilds:
        guild_invs = await guild.invites()
        for i in guild_invs:
            i:discord.Invite
            invites[i.code] = i.uses

# ==============================================================================
# Client Server Commands
# ==============================================================================

def has_permission_role(member:discord.Member):
    path = f'./configs/{member.guild.id}.json'
    if os.path.exists(path):
        with open(path, 'r') as file:
            config = json.load(file)
        try:
            for role in member.roles:
                if role.id == config['mod_role']: return True
                else: return False
        except: 
            return False
    else: return False
        
def has_perms(allow_mods=False,dev_only = False):
    '''Calculate whether or not a member has sufficient permissions for Bridge commands'''
    async def predicate(ctx:discord.ApplicationContext):
        allowance = False
        if dev_only:
            allowance (ctx.guild == dev_guild ) and ctx.author.guild_permissions.administrator
        else:
            admin = ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator
            if allow_mods:    
                allowance = admin or has_permission_role(ctx.author)
            else:
                allowance = admin
        if not allowance:
            raise commands.CheckFailure
        return allowance
    return commands.check(predicate)

def setup_status_embed(guild:discord.Guild) -> discord.Embed():
    path = f'./configs/{guild.id}.json'
    if os.path.exists(path):
        with open(path, 'r') as file:
            config = json.load(file)        
    unset = '❗ **Not set.**'
    set = '↳ **Value set.**'
    embed=discord.Embed(title=f'⟶ {guild.name} Setup Status')
    embed.add_field(name='Mod Channel',value='For important reports, updates, and RIT server-wide warnings.',inline=False)
    embed.add_field(name='Log Channel',value='For join logs and non-urgent information.',inline=False)
    embed.add_field(name='Moderator Role',value='Role allowed to use `/report` aside from admins.',inline=False)
    requirements = ['mod_channel','hooks_channel','mod_role']
    f=0
    complete = 0
    for field in embed.fields:
        field.value += '\n'
        try:
            isvalue = config[requirements[f]]
            field.value+=set
            complete +=1
        except:
            field.value+=unset
        f+=1
    if complete ==3:
        embed.set_footer(text='Setup complete.')
        embed.color=discord.Colour.brand_green()
    else:
        embed.set_footer(text='Setup not complete.')
        embed.color=discord.Colour.yellow()
    return embed

async def update_dev_setup_status(guild:discord.Guild):
    try:
        if str(guild.id) in setup_status_panels:
            await setup_status_panels[str(guild.id)].edit(embed=setup_status_embed(guild))
        else:
            setup_status_panels[str(guild.id)] = await dev_logs_channel.send(embed=setup_status_embed(guild))
    except Exception as e:
        print(e)

def setup_embed(guild:discord.Guild) -> discord.Embed():
    completion_icons = [f'https://cdn.discordapp.com/attachments/1107483500384358510/1181641936889712700/1-3.png','https://cdn.discordapp.com/attachments/1107483500384358510/1181641937363677274/2-3.png','https://cdn.discordapp.com/attachments/1107483500384358510/1181641937112027196/3-3.png']
    path = f'./configs/{guild.id}.json'
    if os.path.exists(path):
        with open(path, 'r') as file:
            config = json.load(file)
    unset = '❗ **Not set.**'
    set = '↳ <>'
    embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255),title='⟶ Setup')
    embed.add_field(name='Mod Channel',value='For important reports, updates, and RIT server-wide warnings.',inline=False)
    embed.add_field(name='Log Channel',value='For join logs and non-urgent information.',inline=False)
    embed.add_field(name='Moderator Role',value='Role allowed to use `/report` aside from admins.',inline=False)
    requirements = ['mod_channel','hooks_channel','mod_role']
    f=0
    complete = 0
    for field in embed.fields:
        field.value += '\n'
        try:
            if f==2:field.value+=set.replace('<>',f'<@&{config[requirements[f]]}>')
            else: field.value+=set.replace('<>',f'<#{config[requirements[f]]}>')
            complete +=1
        except:
            field.value+=unset
            if f==2:field.value+=' Please run `/config setmodrole`'
            else: field.value+=' Please run `/config setchannel`'
        f+=1
    if complete !=0:
        embed.set_footer(icon_url=completion_icons[complete-1],text=f'{((complete/3)*100):.0f}% complete')
    else:
        embed.set_footer(text=f'{((complete/3)*100):.0f}% complete')
    return embed

@bot.slash_command(guild_ids=guilds)
@has_perms()
async def setup(ctx: discord.ApplicationContext):
    '''Bridge Setup'''
    await ctx.guild.get_member(bot.user.id).edit(nick='Bridge')
    await ctx.respond('## Welcome to Bridge.')
    try:
        setup_panels[str(ctx.guild.id)] = await ctx.channel.send(embed=setup_embed(ctx.guild))
    except:
        ctx.respond('Unable to send setup embed. Please check permissions.')
    await update_dev_setup_status(ctx.guild)

async def initial_ban(channel:discord.TextChannel):
    await channel.send('# Setup complete.\nThis next step involves preemptively banning known alternative accounts. This may take some time. Please wait.')
    i = await ban_alt_list(channel.guild,reason_message='An existing alternative account was found on your server.')
    channel_mod = await fetch_mod_channel(channel.guild)
    await channel_mod.send(f'### ⟶ Preemptively banned **{i}** unbanned alternative accounts.\nIf any more are found in the future, they will be banned automatically.')

def write_config_value(guild:discord.Guild,variable:str,value):
    '''Write config values and return if initial ban should be run'''
    data = {}
    path = f'./configs/{guild.id}.json'
    if os.path.exists(path):
        with open(path, 'r') as file:
            data = json.load(file)
    prev_len = len(data)
    with open(path, 'w') as f:
        data[variable] = value
        json.dump(data, f, indent=4)
    if len(data) == 3 and prev_len ==2:
        return True
    return False

config = discord.SlashCommandGroup("config", "Bridge configuration commands")

@config.command(guild_ids=guilds)
async def setchannel(ctx: discord.ApplicationContext, option: discord.Option(str, choices=['Mod Channel', 'Log Channel']), value: discord.Option(discord.TextChannel)):
    '''Set the Mod or Log channel'''
    if not value.permissions_for(ctx.guild.me).view_channel or not value.permissions_for(ctx.guild.me).send_messages or not value.permissions_for(ctx.guild.me).embed_links:
        await ctx.respond("Invalid channel. Please check its permissions and make sure Bridge can view and send messages in it.", ephemeral=True)
        return
    json_names = {
        'Mod Channel': 'mod_channel',
        'Log Channel': 'hooks_channel'
    }
    do_initial_ban = write_config_value(ctx.guild, json_names[option], value.id)
    await ctx.defer()
    if str(ctx.guild.id) in setup_panels:
        try:
            await setup_panels[str(ctx.guild.id)].edit(embed=setup_embed(ctx.guild))
        except Exception as e:
            print(e)
    await ctx.respond('Configuration updated.', ephemeral=True, delete_after=1)
    if do_initial_ban:await initial_ban(ctx.channel)
    await update_dev_setup_status(ctx.guild)

@config.command(guild_ids=guilds)
@has_perms()
async def setmodrole(ctx: discord.ApplicationContext,value:discord.Role):
    '''Set the Mod or Log channel'''
    do_initial_ban = write_config_value(ctx.guild,'mod_role',value.id)
    await ctx.defer()
    if str(ctx.guild.id) in setup_panels:
        try:
            await setup_panels[str(ctx.guild.id)].edit(embed=setup_embed(ctx.guild))
        except Exception as e:
            print(e)
    await ctx.respond('Configuration updated.',ephemeral=True,delete_after=1)
    if do_initial_ban: await initial_ban(ctx.channel)
    await update_dev_setup_status(ctx.guild)

bot.add_application_command(config)

@bot.slash_command(guild_ids=guilds)
async def report(ctx:discord.ApplicationContext,member:discord.Option(discord.Member,description='Mention the account to report'),reason:discord.Option(str,description='Describe what unusual activity occurred.')):
    '''Report a suspected alternative or spam account.'''
    mod_role = await fetch_mod_role(ctx.guild)
    if mod_role in ctx.author.roles or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
        try:
            report = discord.Embed(title='⟶ __New alt reported.__',color=discord.Colour.red
            (),timestamp=datetime.datetime.now())
            nl='\n' # f-string newline workaround
            report.description=f'**From:** {member.guild.name}{nl}{nl}'
            other_servers = []
            for guild in bot.guilds:
                if member in guild.members:
                    other_servers.append(guild.name)
            sep='\n- '
            if len(other_servers)!=0:
                report.description += f'Appears in **{len(other_servers)}** servers:\n- {sep.join(other_servers)}'
            report.add_field(name='Reason',value=reason,inline=False)
            report.add_field(name='ID',value=member.id,inline=False)
            report.set_thumbnail(url=member.avatar.url) 
            report.add_field(name='Name',value=member.name)
            report.add_field(name='Mention',value=f'<@{member.id}>')
            report.add_field(name='Report Author',value=f'<@{ctx.author.id}> ({ctx.author.name})',inline=False)

            await dev_reports_channel.send(embed=report)
            await ctx.respond('Thank you. A report has been sent to the Bridge management server.')
        except Exception as e: 
            await ctx.respond(f'Something went wrong while processing your request. Please contact the Bridge management server if this is a bug.```{e}```')
    else:
        await ctx.respond('You do not have access to this command.')
        
# ==============================================================================
# Developer Utilities
# ==============================================================================
bms = discord.SlashCommandGroup("bms", "Bridge Management Server commands",guild_ids=guilds)

async def global_ban_refresh():
    banlist = verif.fetch_banlist() # passed in here to avoid fetching len(bot.guilds) times
    for guild in bot.guilds:
        await ban_alt_list(guild,banned_ids=banlist)

@bms.command(guild_ids=guilds)
@has_perms(dev_only=True)
async def crossban(ctx:discord.ApplicationContext,ban_id):
    '''For Bridge management server use.'''
    verif.add_to_banlist(ban_id)
    await ctx.respond(f'Added <@{ban_id}> to ritV database.\n- Running global ban refresh.')
    await global_ban_refresh()

@bms.command(guild_ids=guilds)
@has_perms(dev_only=True)
async def globalrefresh(ctx:discord.ApplicationContext):
    await ctx.respond(f'Refreshing bans globally. This will take some time.')
    await global_ban_refresh()
    await ctx.channel.send(f'Done.')

@bms.command(guild_ids=guilds)
@has_perms(dev_only=True)
async def update_from_json(ctx:discord.ApplicationContext):
    '''For Bridge management server use.'''
    current_list = verif.fetch_banlist()
    banlistct = 0
    await ctx.respond('Working...')
    try:
        with open('populate.json', 'r') as file:
            fill = json.load(file)        
            for alt in fill:
                if alt not in current_list:
                    verif.add_to_banlist(alt)
                    banlistct +=1
        await ctx.respond(f'Added **{banlistct}** alts to ritV database.\nRun `/bms globalrefresh` to apply changes.')
    except:
        await ctx.respond('`populate.json` not found in CWD or is incorrectly formatted.')

# ==============================================================================
# Events
# ==============================================================================

@bot.event
async def on_member_join(member: discord.Member):
    newinvites = await member.guild.invites()
    for i in newinvites:
        if invites[i.code] < i.uses:
            channel_hooks = await fetch_hooks_channel(member.guild)
            
            donotping=channel_hooks.members
            if i.inviter not in donotping:
                inviter_id = f'<@{i.inviter.id}>'
            else:
                inviter_id = i.inviter.name
            embed = discord.Embed(title=f"{member.name} joined the server.",color=discord.Colour.blurple(),timestamp=datetime.datetime.now())
            embed.set_thumbnail(url=member.avatar.url) 
            embed.add_field(name='Name',value=member.name)
            embed.add_field(name='Account Creation Date', value=member.created_at.strftime("%m/%d/%Y, %I:%M:%S %p"))
            embed.add_field(name='Mention',value=f'<@{member.id}>')
            embed.add_field(name='Invited by:', value=f'<@{inviter_id}>')
            embed.add_field(name='Invite code:', value=f'`{i.code}`')
            try:
                await channel_hooks.send(embed=embed)
            except:
                console.print('Failed to send invite log to log channel.')
            break
    for i in newinvites:
        invites[i.code] = i.approximate_member_count
    if verif.check_banlist(member.id):
        await member.ban()
        await memberAlert('A user on the ban list was removed.', member)

@bot.event
async def on_command_error(ctx:discord.ApplicationContext, error:discord.DiscordException): # wip error handling. needs some debugging
    if isinstance(error, discord.errors.CheckFailure) or isinstance(error, commands.CheckFailure) or isinstance(error, commands.CheckAnyFailure):
        await ctx.respond(f'### You don\'t have permission to run that command.`/{ctx.command.name}` is only available to server owners and administrators.\n*To learn more about this bot, click [here](https://github.com/mae-su/bridge/)*',ephemeral=True)
    else:
        await ctx.respond('### Yikes!\nAn error occured when running this command. The developers have been notified.',ephemeral=True)
        print(f'A slash command error occurred in {ctx.guild.name}:\n  {error}',style=styles.critical_error)
        error_embed = discord.Embed(title=f'A slash command error occured in {ctx.guild.name}', color=discord.Color.red())
        error_embed.add_field(name='Attempted slash command', value=ctx.command.name if ctx.command else 'None', inline=False)
        error_embed.add_field(name='Ran by', value=f'{ctx.author.name} <@{ctx.author.id}>', inline=False)
        error_embed.add_field(name='Error', value=str(error), inline=False)
        await dev_logs_channel.send('<@275318661647171584>',embed=error_embed)

client_server_commands = [report, config, setup]
dev_commands = [report, config, setup, bms]

@bot.event
async def on_guild_join(guild:discord.Guild):
    print('New server joined.',style=styles.success)
    try:
        await update_dev_setup_status(guild)
    except Exception as e:
        print(e)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{len(bot.guilds)} RIT servers.'))
    console.print(f' ↳ Syncing universal commands to {guild.name} ...',style=styles.working)
    await guild.get_member(bot.user.id).edit(nick='Bridge - run /setup')
    await bot.sync_commands(commands=client_server_commands,guild_ids = [guild.id]) 
    try:
        update_dev_setup_status(guild)
    except Exception as e:
        console.print(f' ↳ [b]Error when attempting to send dev setup status:[/b]',style=styles.critical_error)
        console.print(f'     {e}',style=styles.critical_error)
    console.print(f' ↳ Done. [b]{guild.name}[/b] is ready to run setup',style=styles.success)

@bot.event
async def on_ready():
    console.print('[ul]Bot is loading.[/ul]')
    
    guild_ids = [guild.id for guild in bot.guilds]
    console.print(f'Syncing commands...')
    if not debug_args.no_resync:
        console.print(f' ↳ Syncing universal commands...',style=styles.working)
        await bot.sync_commands(commands=client_server_commands,guild_ids = guild_ids)
    else:
        console.print(f' ↳ --no-resync enabled: Commands only syncing in dev guild.',style=styles.working)
    console.print(f' ↳ Syncing dev server commands...',style=styles.working)
    bot.add_application_command(bms)
    await bot.sync_commands(commands=dev_commands,guild_ids = guilds) 
    console.print(f'Fetching dev guild channels/roles...',style=styles.working)
    global dev_guild,dev_reports_channel,dev_role,dev_logs_channel
    dev_guild = await bot.fetch_guild(1182047934750142524)
    dev_reports_channel = await dev_guild.fetch_channel(1182056826997587979)
    dev_logs_channel = await dev_guild.fetch_channel(1182073430548422676)
    dev_role = await dev_guild._fetch_role(1182053347801436270)
    console.print('Fetching invites...',style=styles.working)
    guild_invs = []
    for guild in bot.guilds:
        guild_invs += await guild.invites()
    for i in guild_invs:
        i:discord.Invite
        invites[i.code] = i.uses
    console.print(f' ↳ {len(invites)} invites loaded.',style=styles.working)
    refreshInvites.start()
    console.print(' ↳ Invite refresh timer started.',style=styles.working)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{len(bot.guilds)} RIT servers.'))
    console.print(f'Completed self setup![bold][orange] Bot is ready.[/orange][not bold]',style=styles.success)

while True:
    try:
        bot.run(token)
    except aiohttp.client_exceptions.ClientConnectorError:
        console.print("↳ Failed to connect. Retrying in a few seconds.")
        time.sleep(5)
