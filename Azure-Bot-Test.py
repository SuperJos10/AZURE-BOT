import discord
from discord import app_commands, Interaction, Embed, ButtonStyle, TextChannel
from discord.ui import View, Button
from discord.utils import get
from discord.ext import commands
import aiohttp
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 703173684608630875
LISTINGS_FILE = "listings.json"

listings = {}
def save_listings():
    with open(LISTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(listings, f, ensure_ascii=False, indent=4)

def load_listings():
    global listings
    if os.path.exists(LISTINGS_FILE):
        with open(LISTINGS_FILE, "r", encoding="utf-8") as f:
            listings = json.load(f)
    else:
        listings = {}

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()
load_listings()

@client.tree.command(name="help", description="Displays a list of available commands")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**Public Commands:**\n"
        "/stock - See a list of available accounts ^^\n"
        "/view-listing [username] - View an account in stock\n"
        "/calculate-tax [amount] - Calculates Robux tax\n"
        "/ez-bot-badge - Simple command to help me maintain my developer badge\n"
        "\n"
        "**Owner Commands:**\n"
        "/add-listing [username] [file] - Add listings to stock with content\n"
        "/remove-listing [username] - Remove listings from stock\n"
        "/edit-listing [username] - Edit the content file of a listing\n"
        "/purge [amount] - Purges a specific amount of messages in a channel\n"
        "/dm [user] [message] - DM a user with any message\n"
        "/bot-status [online/offline/maintenance/error] - Set the bot status\n"
        "/setup-ticket - Sets up the ticket UI"
    )
    await interaction.response.send_message(help_text)

@client.tree.command(name="add-listing", description="Owner-only: Add a new listing with a file upload")
@app_commands.describe(username="Username to list", file="Upload a .txt file containing the listing content")
async def add_listing(interaction: discord.Interaction, username: str, file: discord.Attachment):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    if not file.filename.endswith(".txt"):
        await interaction.response.send_message("❌ Please upload a `.txt` file!", ephemeral=True)
        return

    file_content = await file.read()
    text_content = file_content.decode("utf-8")

    listings[username.lower()] = text_content
    save_listings()
    await interaction.response.send_message(f"✅ Listing for `{username}` added.")

@client.tree.command(name="stock", description="View all available listings")
async def stock(interaction: discord.Interaction):
    if not listings:
        await interaction.response.send_message("❌ No listings available.")
    else:
        stock_list = "\n".join(f"- {user}" for user in listings)
        await interaction.response.send_message(f"📦 **Current Stock:**\n{stock_list}")

@client.tree.command(name="view-listing", description="View listing details for a specific user")
@app_commands.describe(username="Username to view")
async def view_listing(interaction: discord.Interaction, username: str):
    username = username.lower()
    if username not in listings:
        await interaction.response.send_message(f"❌ No listing found for `{username}`.")
        return

    content = listings[username]

    if not content:
        await interaction.response.send_message("❌ This listing has no content.")
        return

    title_format = f"📄 **Listing for `{username}`**\n\n"
    max_length = 2000 - len(title_format)
    
    chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]

    for i, chunk in enumerate(chunks):
        if i == 0:
            await interaction.response.send_message(f"{title_format}{chunk}")
        else:
            await interaction.followup.send(f"{title_format}{chunk}")

@client.tree.command(name="remove-listing", description="Owner-only: Remove a listing by username")
@app_commands.describe(username="Username to remove")
async def remove_listing(interaction: discord.Interaction, username: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    username = username.lower()
    if username not in listings:
        await interaction.response.send_message(f"❌ No listing found for `{username}`.")
    else:
        del listings[username]
        await interaction.response.send_message(f"🗑️ Listing for `{username}` has been removed.")

@client.tree.command(name="edit-listing", description="Owner-only: Edit an existing listing with a new file")
@app_commands.describe(username="Username to edit", file="Upload a new .txt file containing the updated content")
async def edit_listing(interaction: discord.Interaction, username: str, file: discord.Attachment):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    username = username.lower()
    if username not in listings:
        await interaction.response.send_message(f"❌ No listing found for `{username}` to edit.", ephemeral=True)
        return

    if not file.filename.endswith(".txt"):
        await interaction.response.send_message("❌ Please upload a `.txt` file!", ephemeral=True)
        return

    file_content = await file.read()
    text_content = file_content.decode("utf-8")

    listings[username] = text_content
    await interaction.response.send_message(f"✅ Listing for `{username}` has been updated.")

@client.tree.command(name="purge", description="Owner-only: Purge a number of messages from the channel")
@app_commands.describe(amount="Number of messages to delete")
async def purge(interaction: discord.Interaction, amount: int):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Please choose a number between 1 and 100.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    def check(message):
        return message.author != interaction.user or message.content != "/purge"

    await interaction.channel.purge(limit=amount, check=check)

    await interaction.followup.send(f"✅ Deleted {amount} messages.", ephemeral=True)

@client.tree.command(name="dm", description="Owner-only: DM a user with a custom message 💌")
@app_commands.describe(user="The user to DM", message="The message you want to send")
async def dm(interaction: discord.Interaction, user: discord.User, message: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    try:
        await user.send(message)
        await interaction.response.send_message(f"✅ Successfully sent a DM to {user.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ I can't DM {user.mention} (maybe they have DMs closed!).", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to send DM. Error: {e}", ephemeral=True)

STATUS_VOICE_CHANNEL_ID = 1365673489503227914

@client.tree.command(name="bot-status", description="Owner-only: Set the bot's status.")
@commands.cooldown(1, 30, commands.BucketType.guild)
async def bot_status(interaction: discord.Interaction, status: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    voice_channel = interaction.guild.get_channel(STATUS_VOICE_CHANNEL_ID)

    if not voice_channel:
        await interaction.response.send_message("❌ Couldn't find the status voice channel.", ephemeral=True)
        return

    status_dict = {
        "online": "🟢AZURE-BOT STATUS🟢",
        "offline": "🔴AZURE-BOT STATUS🔴",
        "maintenance": "⚠️AZURE-BOT STATUS⚠️",
        "error": "❌AZURE-BOT STATUS❌"
    }

    if status not in status_dict:
        await interaction.response.send_message("❌ Invalid status. Please choose from 'online', 'offline', 'maintenance', or 'error'.", ephemeral=True)
        return

    await voice_channel.edit(name=status_dict[status])
    await interaction.response.send_message(f"✅ Bot status updated to **{status.capitalize()}**.", ephemeral=True)
    pass

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Please wait {round(error.retry_after, 1)} seconds before using this command again.", ephemeral=True)

@client.tree.command(name="ez-bot-badge", description="HELP ME MAINTAIN MY BADGE ❤️")
async def ez_bot_badge(interaction: discord.Interaction):
    await interaction.response.send_message("THANK YOU XOXO - BK_X", ephemeral=True)
    return

@client.tree.command(name="calculate-tax", description="Calculates before and after tax amounts based on Roblox tax rates")
@app_commands.describe(amount="Amount to calculate the tax for")
async def calculate_tax(interaction: discord.Interaction, amount: float):
    tax_rate = 0.30

    sell_price = amount / (1 - tax_rate)
    receive_amount = amount * (1 - tax_rate)

    response = (
        f"**Tax Calculation for {amount} Robux**\n"
        f"Before Tax: {sell_price:.2f} Robux\n"
        f"After Tax: {receive_amount:.2f} Robux"
    )

    await interaction.response.send_message(response)
  
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(
            label="Support/Question Ticket",
            style=ButtonStyle.primary,
            custom_id="support_ticket"
        ))
        self.add_item(Button(
            label="DWC Ticket",
            style=ButtonStyle.secondary,
            custom_id="dwc_ticket"
        ))

@client.tree.command(name="setup-ticket", description="Owner-only: Setup the ticket message with buttons 💌")
async def setup_ticket(interaction: Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    embed = Embed(
        title="🎟️ Create a Ticket",
        description="Need help? Have a question? Want to discuss something? 💬\n\nChoose the appropriate button below to open a ticket with our team!",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="DWC - Deal With Caution (Scammers)")

    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Ticket system setup successfully!", ephemeral=True)

@client.event
async def on_interaction(interaction: Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data['custom_id'] == "support_ticket":
            channel_name = f"support-{interaction.user.name}"
            category = get(interaction.guild.categories, name="Important")
            overwrites = {
                interaction.user: discord.PermissionOverwrite(view_channel=True),
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                get(interaction.guild.roles, name="Staff"): discord.PermissionOverwrite(view_channel=True)
            }

            ticket_channel = await interaction.guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

            await ticket_channel.send(f"Hello {interaction.user.mention}, this is your support ticket. Please describe your issue here.")
            await interaction.response.send_message(f"✅ Your **Support** ticket has been created: {ticket_channel.mention}", ephemeral=True)

        elif interaction.data['custom_id'] == "dwc_ticket":
            channel_name = f"dwc-{interaction.user.name}"
            category = get(interaction.guild.categories, name="Important")
            overwrites = {
                interaction.user: discord.PermissionOverwrite(view_channel=True),
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                get(interaction.guild.roles, name="Staff"): discord.PermissionOverwrite(view_channel=True)
            }

            ticket_channel = await interaction.guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

            await ticket_channel.send(f"Hello {interaction.user.mention}, this is your DWC ticket. Please describe your issue here.")
            await interaction.response.send_message(f"✅ Your **DWC** ticket has been created: {ticket_channel.mention}", ephemeral=True)

client.run(TOKEN)
